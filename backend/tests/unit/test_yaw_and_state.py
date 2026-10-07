"""Unit test suite for WindCtrl Validate yaw error and state machine validators."""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.yaw import ControllerStateValidator, YawValidator


def test_yaw_validator_nominal_pass():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "nacelle_yaw_error": np.sin(t) * 2.5,  # Max 2.5 deg <= 10 deg limit
        }
    )
    validator = YawValidator(max_yaw_error_deg=10.0)
    results = validator.validate(df)

    assert all(r.status == ValidationStatus.PASS for r in results)


def test_yaw_validator_excessive_misalignment():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "nacelle_yaw_error": [18.5] * n,  # Severe 18.5 deg misdirection
        }
    )
    validator = YawValidator(max_yaw_error_deg=10.0)
    results = validator.validate(df)

    peak_res = next(r for r in results if r.validator == "yaw.peak_error")
    assert peak_res.status == ValidationStatus.FAIL
    assert peak_res.actual == 18.5


def test_controller_state_illegal_transition():
    df = pd.DataFrame(
        {
            "controller_state": ["IDLE", "RATED_POWER", "RATED_POWER"],  # Illegal direct jump without STARTUP
        }
    )
    validator = ControllerStateValidator()
    results = validator.validate(df)

    trans_res = next(r for r in results if r.validator == "controller_state.transitions")
    assert trans_res.status == ValidationStatus.FAIL
    assert trans_res.actual == 1

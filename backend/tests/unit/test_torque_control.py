"""Unit test suite for WindCtrl Validate generator torque validator."""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.torque_control import TorqueControlValidator


def test_torque_control_nominal_pass():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "generator_torque_nm": [40000.0] * n,
            "controller_state": ["BELOW_RATED"] * n,
            "wind_speed_mps": [10.0] * n,
        }
    )
    validator = TorqueControlValidator()
    results = validator.validate(df)

    assert all(r.status == ValidationStatus.PASS for r in results)


def test_torque_control_negative_motoring_violation():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    torques = [40000.0] * n
    torques[30] = -1500.0  # Invalid motoring torque

    df = pd.DataFrame(
        {
            "timestamp": t,
            "generator_torque_nm": torques,
            "controller_state": ["BELOW_RATED"] * n,
            "wind_speed_mps": [10.0] * n,
        }
    )
    validator = TorqueControlValidator()
    results = validator.validate(df)

    neg_res = next(r for r in results if r.validator == "torque_control.negative_torque")
    assert neg_res.status == ValidationStatus.FAIL
    assert neg_res.actual == 1


def test_torque_control_step_discontinuity_spike():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    torques = [40000.0] * n
    # Spike by 20,000 Nm in 0.05s
    torques[40] = 60000.0
    torques[41] = 60000.0
    torques[42] = 60000.0
    torques[43] = 60000.0
    torques[44] = 60000.0

    df = pd.DataFrame(
        {
            "timestamp": t,
            "generator_torque_nm": torques,
            "controller_state": ["BELOW_RATED"] * n,
            "wind_speed_mps": [10.0] * n,
        }
    )
    validator = TorqueControlValidator(max_torque_rate_nm_s=15000.0)
    results = validator.validate(df)

    spike_res = next(r for r in results if r.validator == "torque_control.torque_spikes")
    assert spike_res.status in (ValidationStatus.WARNING, ValidationStatus.FAIL)

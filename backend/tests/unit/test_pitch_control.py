"""Unit test suite for WindCtrl Validate blade pitch controller validator."""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.pitch_control import PitchControlValidator


def test_pitch_control_nominal_above_rated():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "wind_speed_mps": [14.0] * n,
            "blade_pitch_deg": np.linspace(8.0, 8.5, n),
        }
    )
    validator = PitchControlValidator()
    results = validator.validate(df)

    above_res = next(r for r in results if r.validator == "pitch_control.above_rated_response")
    assert above_res.status == ValidationStatus.PASS
    assert above_res.actual > 2.0


def test_pitch_control_stuck_at_fine_under_high_wind():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "wind_speed_mps": [16.0] * n,  # High wind
            "blade_pitch_deg": [0.0] * n,   # Stuck at fine pitch!
        }
    )
    validator = PitchControlValidator()
    results = validator.validate(df)

    above_res = next(r for r in results if r.validator == "pitch_control.above_rated_response")
    assert above_res.status == ValidationStatus.FAIL

    sat_res = next(r for r in results if r.validator == "pitch_control.saturation_check")
    assert sat_res.status == ValidationStatus.FAIL


def test_pitch_control_excessive_actuator_rate():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    pitch = [0.0] * n
    # Jump 15 degrees in 0.05s -> rate = 300 deg/s
    pitch[20] = 15.0

    df = pd.DataFrame(
        {
            "timestamp": t,
            "wind_speed_mps": [10.0] * n,
            "blade_pitch_deg": pitch,
        }
    )
    validator = PitchControlValidator(max_pitch_rate_dps=8.0)
    results = validator.validate(df)

    rate_res = next(r for r in results if r.validator == "pitch_control.actuator_rate_limit")
    assert rate_res.status in (ValidationStatus.WARNING, ValidationStatus.FAIL)
    assert rate_res.actual > 8.0

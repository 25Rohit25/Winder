"""Unit test suite for WindCtrl Validate rotor speed validator."""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.rotor_speed import RotorSpeedValidator


@pytest.fixture
def nominal_rotor_df() -> pd.DataFrame:
    n = 100
    t = np.linspace(0.0, 5.0, n)
    return pd.DataFrame(
        {
            "timestamp": t,
            "rotor_speed_rpm": np.linspace(11.0, 12.1, n),
            "generator_speed_rpm": np.linspace(11.0 * 97.0, 12.1 * 97.0, n),
            "controller_state": ["BELOW_RATED"] * n,
        }
    )


def test_rotor_speed_nominal_pass(nominal_rotor_df: pd.DataFrame):
    validator = RotorSpeedValidator()
    results = validator.validate(nominal_rotor_df)

    assert len(results) >= 2
    assert all(r.status == ValidationStatus.PASS for r in results)


def test_rotor_speed_excessive_acceleration(nominal_rotor_df: pd.DataFrame):
    df = nominal_rotor_df.copy()
    # Step change from 11.0 to 14.0 RPM in 0.05s -> accel = 60 RPM/s
    df.loc[20, "rotor_speed_rpm"] = 14.0

    validator = RotorSpeedValidator(max_accel_rpm_s=1.5)
    results = validator.validate(df)

    accel_result = next(r for r in results if r.validator == "rotor_speed.rate_of_change")
    assert accel_result.status in (ValidationStatus.WARNING, ValidationStatus.FAIL)
    assert accel_result.actual > 1.5


def test_rotor_speed_gearbox_ratio_mismatch(nominal_rotor_df: pd.DataFrame):
    df = nominal_rotor_df.copy()
    # Alter generator speed so ratio drops to 80 instead of 97
    df["generator_speed_rpm"] = df["rotor_speed_rpm"] * 80.0

    validator = RotorSpeedValidator(gearbox_ratio=97.0)
    results = validator.validate(df)

    gear_result = next(r for r in results if r.validator == "rotor_speed.gearbox_ratio")
    assert gear_result.status == ValidationStatus.FAIL
    assert gear_result.actual > 2.5

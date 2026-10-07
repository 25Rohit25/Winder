"""Unit test suite for WindCtrl Validate signal integrity validator."""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.signal_integrity import SignalIntegrityValidator


@pytest.fixture
def clean_telemetry_df() -> pd.DataFrame:
    """Fixture providing clean, valid baseline telemetry."""
    n = 100
    t = np.linspace(0.0, 5.0, n)
    return pd.DataFrame(
        {
            "timestamp": t,
            "wind_speed_mps": np.linspace(8.0, 10.0, n),
            "rotor_speed_rpm": np.linspace(10.0, 11.5, n),
            "generator_speed_rpm": np.linspace(970.0, 1115.5, n),
            "generator_torque_nm": np.linspace(35000.0, 40000.0, n),
            "blade_pitch_deg": np.zeros(n),
            "electrical_power_kw": np.linspace(3000.0, 4200.0, n),
            "tower_acceleration": np.zeros(n),
            "nacelle_yaw_error": np.zeros(n),
            "controller_state": ["BELOW_RATED"] * n,
            "fault_flags": [0] * n,
        }
    )


def test_signal_integrity_clean_pass(clean_telemetry_df: pd.DataFrame):
    validator = SignalIntegrityValidator(dt_nominal=0.05)
    results = validator.validate(clean_telemetry_df)

    assert len(results) > 0
    # On clean telemetry, no check should fail
    assert all(r.status == ValidationStatus.PASS for r in results)


def test_signal_integrity_empty_dataframe():
    validator = SignalIntegrityValidator()
    results = validator.validate(pd.DataFrame())

    assert len(results) == 1
    assert results[0].status == ValidationStatus.FAIL
    assert results[0].metric == "dataset_row_count"


def test_signal_integrity_nan_dropout(clean_telemetry_df: pd.DataFrame):
    df = clean_telemetry_df.copy()
    # Inject 5% NaNs into wind speed
    df.loc[10:15, "wind_speed_mps"] = np.nan

    validator = SignalIntegrityValidator()
    results = validator.validate(df)

    nan_result = next(r for r in results if r.validator == "signal_integrity.nan_dropout")
    assert nan_result.status in (ValidationStatus.WARNING, ValidationStatus.FAIL)
    assert nan_result.actual > 0


def test_signal_integrity_duplicate_timestamps(clean_telemetry_df: pd.DataFrame):
    df = clean_telemetry_df.copy()
    df.loc[5, "timestamp"] = df.loc[4, "timestamp"]  # duplicate

    validator = SignalIntegrityValidator()
    results = validator.validate(df)

    dup_result = next(r for r in results if r.validator == "signal_integrity.timestamp_duplicates")
    assert dup_result.status == ValidationStatus.FAIL
    assert dup_result.actual == 1


def test_signal_integrity_non_monotonic_timestamps(clean_telemetry_df: pd.DataFrame):
    df = clean_telemetry_df.copy()
    df.loc[10, "timestamp"] = 0.1  # retroactive jump backwards

    validator = SignalIntegrityValidator()
    results = validator.validate(df)

    jump_result = next(r for r in results if r.validator == "signal_integrity.time_continuity")
    assert jump_result.status == ValidationStatus.FAIL
    assert jump_result.actual > 0


def test_signal_integrity_negative_wind_speed(clean_telemetry_df: pd.DataFrame):
    df = clean_telemetry_df.copy()
    df.loc[20, "wind_speed_mps"] = -5.0

    validator = SignalIntegrityValidator()
    results = validator.validate(df)

    ws_result = next(r for r in results if r.validator == "signal_integrity.wind_speed_range")
    assert ws_result.status == ValidationStatus.FAIL
    assert ws_result.actual == 1


def test_signal_integrity_sensor_freeze(clean_telemetry_df: pd.DataFrame):
    # Repeat static value across 60 samples
    df = clean_telemetry_df.copy()
    df["wind_speed_mps"] = 8.5  # Completely static zero-variance

    validator = SignalIntegrityValidator()
    results = validator.validate(df)

    freeze_result = next(r for r in results if r.validator == "signal_integrity.sensor_freeze")
    assert freeze_result.status == ValidationStatus.FAIL
    assert freeze_result.actual > 0

"""Hypothesis property-based tests verifying numerical invariance and scoring properties."""

import hypothesis.strategies as st
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings as hyp_settings

from backend.app.models.validation import ValidationStatus
from backend.app.services.metrics import compute_validation_score
from backend.app.utils.conversions import rad_per_sec_to_rpm, rpm_to_rad_per_sec
from backend.app.validators.overspeed import OverspeedValidator
from backend.app.validators.power_curve import PowerCurveValidator


@given(
    passed=st.integers(min_value=0, max_value=100),
    warnings=st.integers(min_value=0, max_value=100),
    failed=st.integers(min_value=0, max_value=100),
)
@hyp_settings(max_examples=100)
def test_validation_score_bounded_in_range(passed: int, warnings: int, failed: int):
    """Property: Overall validation score must be strictly bounded in [0.0, 100.0]."""
    total = passed + warnings + failed
    score = compute_validation_score(passed, warnings, failed, total)
    assert 0.0 <= score <= 100.0


@given(
    passed=st.integers(min_value=1, max_value=50),
    warnings=st.integers(min_value=0, max_value=50),
    failed=st.integers(min_value=0, max_value=50),
)
@hyp_settings(max_examples=100)
def test_validation_score_monotonicity_on_failure(passed: int, warnings: int, failed: int):
    """Property: Converting a passed test to a failed test must never increase the score."""
    total = passed + warnings + failed
    score_before = compute_validation_score(passed, warnings, failed, total)
    score_after = compute_validation_score(passed - 1, warnings, failed + 1, total)
    assert score_after <= score_before


@given(rpm=st.floats(min_value=0.01, max_value=1000.0))
@hyp_settings(max_examples=50)
def test_rpm_conversion_roundtrip_invariance(rpm: float):
    """Property: Roundtrip RPM -> rad/s -> RPM conversion preserves numerical value."""
    rad_s = rpm_to_rad_per_sec(rpm)
    recovered_rpm = rad_per_sec_to_rpm(rad_s)
    assert recovered_rpm == pytest.approx(rpm, rel=1e-5)


@given(
    wind_speed=st.floats(min_value=0.0, max_value=40.0),
    rotor_speed=st.floats(min_value=0.0, max_value=25.0),
)
@hyp_settings(max_examples=50)
def test_overspeed_validator_contract_invariance(wind_speed: float, rotor_speed: float):
    """Property: OverspeedValidator always yields valid enum status and non-null metric."""
    df = pd.DataFrame(
        {
            "timestamp": [0.0, 0.05],
            "wind_speed_mps": [wind_speed, wind_speed],
            "rotor_speed_rpm": [rotor_speed, rotor_speed],
            "controller_state": ["RATED_POWER", "RATED_POWER"],
        }
    )
    validator = OverspeedValidator(operational_ceiling_rpm=14.50, overspeed_trip_rpm=15.00)
    results = validator.validate(df)

    assert len(results) >= 1
    for ev in results:
        assert ev.status in (ValidationStatus.PASS, ValidationStatus.WARNING, ValidationStatus.FAIL)
        assert isinstance(ev.actual, (float, int, str))
        assert ev.metric != ""

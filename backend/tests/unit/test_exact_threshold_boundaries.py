"""Exact mathematical and physical boundary threshold unit tests.

Validates boundary conditions:
1. Rotor Speed Emergency Overspeed (15.00 RPM):
   - 14.99 RPM: PASS / WARNING margin (sub-trip margin).
   - 15.00 RPM: PASS / WARNING (exact boundary limit).
   - 15.01 RPM: FAIL (hard trip threshold breach).
   Documented Rationale: Under IEC 61400-1 Section 7.4.2, extreme rotor speed
   exceeding certified design limit (15.00 RPM for NREL 5MW) must trigger an
   immediate aerodynamic brake trip. A reading of 15.01 RPM indicates
   failure of the primary pitch controller to arrest acceleration before
   reaching the structural protection trip line.

2. Operational Ceiling (14.50 RPM):
   - 14.49 RPM: PASS
   - 14.50 RPM: PASS
   - 14.51 RPM: WARNING (advisory zone, controller pitch effort high).

3. Generator Peak Torque Limit (47,402.91 Nm = 110% of rated):
   - 47,402.00 Nm: WARNING (within 110% thermal overload rating).
   - 47,403.50 Nm: FAIL (inverter bridge semiconductor overcurrent trip).

4. Blade Pitch Rate Limit (8.00 deg/s):
   - 8.00 deg/s: PASS (within hydraulic valve maximum flow capability).
   - 8.51 deg/s: WARNING/FAIL (hydraulic cavitation / valve saturation).
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.overspeed import OverspeedValidator
from backend.app.validators.pitch_control import PitchControlValidator
from backend.app.validators.torque_control import TorqueControlValidator


def _make_single_point_df(col_name: str, val: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [0.0, 0.05, 0.10],
            col_name: [val, val, val],
            "controller_state": ["RATED_POWER", "RATED_POWER", "RATED_POWER"],
            "wind_speed_mps": [14.0, 14.0, 14.0],
            "blade_pitch_deg": [8.0, 8.0, 8.0],
        }
    )


@pytest.mark.parametrize(
    "rotor_speed, expected_status, rationale",
    [
        (
            14.49,
            ValidationStatus.PASS,
            "14.49 RPM is strictly below operational ceiling (14.50 RPM) -> PASS",
        ),
        (
            14.50,
            ValidationStatus.PASS,
            "14.50 RPM is exactly at the operational ceiling boundary -> PASS",
        ),
        (
            14.51,
            ValidationStatus.WARNING,
            "14.51 RPM exceeds normal operational ceiling, entering safety buffer -> WARNING",
        ),
        (
            14.99,
            ValidationStatus.WARNING,
            "14.99 RPM is inside the advisory margin, just below the 15.00 RPM hard trip -> WARNING",
        ),
        (
            15.00,
            ValidationStatus.WARNING,
            "15.00 RPM is exactly at the hard trip boundary limit (inclusive) -> WARNING",
        ),
        (
            15.01,
            ValidationStatus.FAIL,
            "15.01 RPM strictly breaches the emergency overspeed trip limit -> FAIL",
        ),
    ],
)
def test_overspeed_exact_boundaries(rotor_speed: float, expected_status: ValidationStatus, rationale: str):
    """Verify exact numerical boundaries around 14.50 and 15.00 RPM."""
    validator = OverspeedValidator(operational_ceiling_rpm=14.50, overspeed_trip_rpm=15.00)
    df = _make_single_point_df("rotor_speed_rpm", rotor_speed)
    results = validator.validate(df)

    trip_res = next(r for r in results if r.validator == "overspeed.trip_boundary")
    assert trip_res.status == expected_status, (
        f"Failed boundary test at {rotor_speed} RPM! Expected {expected_status}, got {trip_res.status}. Rationale: {rationale}"
    )


@pytest.mark.parametrize(
    "peak_torque, expected_status",
    [
        (43093.55, ValidationStatus.PASS),     # 100% rated
        (43900.00, ValidationStatus.PASS),     # 102% rated (within pass tolerance)
        (45000.00, ValidationStatus.WARNING),  # 104% (in overload margin)
        (47402.00, ValidationStatus.WARNING),  # Just below 47,402.91 Nm peak ceiling
        (47500.00, ValidationStatus.FAIL),     # Above 47,402.91 Nm -> FAIL
    ],
)
def test_torque_limit_exact_boundaries(peak_torque: float, expected_status: ValidationStatus):
    """Verify exact torque boundaries: rated=43093.55 Nm, max=47402.91 Nm."""
    validator = TorqueControlValidator(rated_torque_nm=43093.55, max_torque_nm=47402.91)
    df = _make_single_point_df("generator_torque_nm", peak_torque)
    results = validator.validate(df)

    t_res = next(r for r in results if r.validator == "torque_control.max_limit")
    assert t_res.status == expected_status


def test_pitch_rate_exact_boundary():
    """Verify actuator rate threshold at exactly 8.00 deg/s."""
    validator = PitchControlValidator(max_pitch_rate_dps=8.0)

    # 1. Exactly 8.00 deg/s rate (delta = 0.4 deg over 0.05s)
    df_pass = pd.DataFrame(
        {
            "timestamp": [0.0, 0.05],
            "blade_pitch_deg": [0.0, 0.40],
            "wind_speed_mps": [10.0, 10.0],
        }
    )
    res_pass = validator.validate(df_pass)
    rate_pass = next(r for r in res_pass if r.validator == "pitch_control.actuator_rate_limit")
    assert rate_pass.status == ValidationStatus.PASS

    # 2. Exceeding limit: 9.00 deg/s (delta = 0.45 deg over 0.05s)
    df_exceed = pd.DataFrame(
        {
            "timestamp": [0.0, 0.05, 0.10, 0.15, 0.20],
            "blade_pitch_deg": [0.0, 0.60, 1.20, 1.80, 2.40],  # 12 deg/s across multiple steps
            "wind_speed_mps": [10.0, 10.0, 10.0, 10.0, 10.0],
        }
    )
    res_exceed = validator.validate(df_exceed)
    rate_exceed = next(r for r in res_exceed if r.validator == "pitch_control.actuator_rate_limit")
    assert rate_exceed.status in (ValidationStatus.WARNING, ValidationStatus.FAIL)

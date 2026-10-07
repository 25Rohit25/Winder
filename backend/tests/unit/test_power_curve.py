"""Unit test suite for WindCtrl Validate IEC 61400-12 power curve validator."""

import numpy as np
import pandas as pd
import pytest

from backend.app.models.validation import ValidationStatus
from backend.app.validators.power_curve import PowerCurveValidator, reference_nrel_5mw_power_curve


def test_reference_power_curve_characteristics():
    assert reference_nrel_5mw_power_curve(2.5) == 0.0      # Sub cut-in
    assert reference_nrel_5mw_power_curve(11.4) == 5000.0   # Rated wind
    assert reference_nrel_5mw_power_curve(18.0) == 5000.0   # Above rated
    assert reference_nrel_5mw_power_curve(26.0) == 0.0      # Cut-out
    assert 0.0 < reference_nrel_5mw_power_curve(8.0) < 5000.0


def test_power_curve_rated_tracking_pass():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "wind_speed_mps": [14.0] * n,
            "electrical_power_kw": np.linspace(4980.0, 5020.0, n),
            "controller_state": ["RATED_POWER"] * n,
        }
    )
    validator = PowerCurveValidator()
    results = validator.validate(df)

    cap_res = next(r for r in results if r.validator == "power_curve.rated_power_cap")
    assert cap_res.status == ValidationStatus.PASS
    assert cap_res.actual < 2.0


def test_power_curve_underperformance_fail():
    n = 100
    t = np.linspace(0.0, 5.0, n)
    # At 15 m/s wind, power should be 5000 kW, but only produces 3200 kW (36% deficit)
    df = pd.DataFrame(
        {
            "timestamp": t,
            "wind_speed_mps": [15.0] * n,
            "electrical_power_kw": [3200.0] * n,
            "controller_state": ["RATED_POWER"] * n,
        }
    )
    validator = PowerCurveValidator()
    results = validator.validate(df)

    cap_res = next(r for r in results if r.validator == "power_curve.rated_power_cap")
    assert cap_res.status == ValidationStatus.FAIL
    assert cap_res.actual > 12.0

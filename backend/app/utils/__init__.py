"""Utilities and helpers for WindCtrl Validate."""

from backend.app.utils.conversions import (
    deg_to_rad,
    kw_to_mw,
    nm_to_knm,
    rad_per_sec_to_rpm,
    rad_to_deg,
    rpm_to_rad_per_sec,
)
from backend.app.utils.math_helpers import (
    calculate_power_coefficient_cp,
    compute_moving_rms,
    compute_rate_of_change,
    detect_step_discontinuities,
)

__all__ = [
    "rpm_to_rad_per_sec",
    "rad_per_sec_to_rpm",
    "deg_to_rad",
    "rad_to_deg",
    "nm_to_knm",
    "kw_to_mw",
    "compute_rate_of_change",
    "compute_moving_rms",
    "detect_step_discontinuities",
    "calculate_power_coefficient_cp",
]

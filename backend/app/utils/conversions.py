"""Engineering unit conversion utilities for wind turbine dynamics."""

import numpy as np


def rpm_to_rad_per_sec(rpm: float) -> float:
    """Convert rotational velocity from RPM to rad/s."""
    return float(rpm * (2.0 * np.pi / 60.0))


def rad_per_sec_to_rpm(rad_per_sec: float) -> float:
    """Convert rotational velocity from rad/s to RPM."""
    return float(rad_per_sec * (60.0 / (2.0 * np.pi)))


def deg_to_rad(degrees: float) -> float:
    """Convert angle from degrees to radians."""
    return float(np.radians(degrees))


def rad_to_deg(radians: float) -> float:
    """Convert angle from radians to degrees."""
    return float(np.degrees(radians))


def nm_to_knm(torque_nm: float) -> float:
    """Convert torque from Nm to kNm."""
    return float(torque_nm / 1000.0)


def kw_to_mw(power_kw: float) -> float:
    """Convert power from kW to MW."""
    return float(power_kw / 1000.0)

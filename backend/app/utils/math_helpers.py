"""Engineering math helpers and numerical utilities."""

import numpy as np
import pandas as pd
from typing import Tuple


def compute_rate_of_change(series: pd.Series, time: pd.Series) -> pd.Series:
    """Compute numerical time derivative (dx/dt) handling non-uniform time delta safely."""
    dt = time.diff().replace(0, np.nan)
    dx = series.diff()
    derivative = dx / dt
    return derivative.bfill().fillna(0.0)


def compute_moving_rms(signal: pd.Series, window_size: int = 10) -> pd.Series:
    """Compute rolling Root Mean Square of a vibration/acceleration signal."""
    return np.sqrt(signal.pow(2).rolling(window=window_size, min_periods=1).mean())


def detect_step_discontinuities(series: pd.Series, threshold: float) -> pd.Series:
    """Flag indices where point-to-point absolute delta exceeds acceptable step limit."""
    diff = series.diff().abs()
    return diff > threshold


def calculate_power_coefficient_cp(
    power_watts: float,
    wind_speed_mps: float,
    rotor_radius_m: float = 63.0,
    air_density_kgpm3: float = 1.225,
) -> float:
    """Calculate aerodynamic rotor power coefficient Cp (Betz limit = 0.593)."""
    if wind_speed_mps <= 0.5:
        return 0.0
    swept_area = np.pi * (rotor_radius_m ** 2)
    p_wind = 0.5 * air_density_kgpm3 * swept_area * (wind_speed_mps ** 3)
    if p_wind <= 0:
        return 0.0
    cp = power_watts / p_wind
    return float(np.clip(cp, 0.0, 0.593))

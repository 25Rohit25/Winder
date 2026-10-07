"""Deterministic synthetic fault injection engine for wind turbine controller testing."""

from enum import Enum
from typing import List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from backend.app.core.exceptions import FaultInjectionError


class FaultType(str, Enum):
    """Catalog of physical and sensor fault injection models."""

    ROTOR_OVERSPEED = "ROTOR_OVERSPEED"
    PITCH_ACTUATOR_DELAY = "PITCH_ACTUATOR_DELAY"
    SENSOR_DROPOUT = "SENSOR_DROPOUT"
    SENSOR_FREEZE = "SENSOR_FREEZE"
    TORQUE_SPIKE = "TORQUE_SPIKE"
    NOISY_WIND_SENSOR = "NOISY_WIND_SENSOR"
    YAW_MISALIGNMENT = "YAW_MISALIGNMENT"
    POWER_UNDERPERFORMANCE = "POWER_UNDERPERFORMANCE"
    TIMESTAMP_GAP = "TIMESTAMP_GAP"
    CONTROLLER_STATE_FAULT = "CONTROLLER_STATE_FAULT"


class FaultConfig(BaseModel):
    """Specification of fault occurrence parameters."""

    fault_type: FaultType
    start_time: float = Field(default=20.0, description="Start time in seconds")
    duration: float = Field(default=10.0, description="Duration of fault in seconds")
    severity: float = Field(default=1.0, ge=0.1, le=5.0, description="Magnitude scaling factor")
    channel: Optional[str] = Field(default=None, description="Optional target channel")


class FaultInjectionEngine:
    """Injects physics-based and sensor-level synthetic anomalies into telemetry datasets."""

    @staticmethod
    def inject_fault(df_in: pd.DataFrame, config: FaultConfig) -> pd.DataFrame:
        """Inject specified fault into dataframe and mark fault bitmask."""
        df = df_in.copy()
        t_start = config.start_time
        t_end = t_start + config.duration
        mask = (df["timestamp"] >= t_start) & (df["timestamp"] <= t_end)

        if not mask.any():
            raise FaultInjectionError(
                f"Injection window [{t_start}s, {t_end}s] outside dataset bounds "
                f"[{df['timestamp'].min()}s, {df['timestamp'].max()}s]"
            )

        # Flag bits for traceability
        fault_bit = 1 << list(FaultType).index(config.fault_type)
        df.loc[mask, "fault_flags"] = df.loc[mask, "fault_flags"] | fault_bit

        if config.fault_type == FaultType.ROTOR_OVERSPEED:
            # Boost rotor speed above 15.00 RPM limit (e.g., 15.3 RPM)
            adder = 2.5 * config.severity
            df.loc[mask, "rotor_speed_rpm"] = df.loc[mask, "rotor_speed_rpm"] + adder
            df.loc[mask, "generator_speed_rpm"] = df.loc[mask, "rotor_speed_rpm"] * 97.0

        elif config.fault_type == FaultType.PITCH_ACTUATOR_DELAY:
            # Lag pitch angle backwards by shifting or freezing near fine pitch
            lag_steps = max(10, int(config.severity * 20))
            pitched_slice = df.loc[mask, "blade_pitch_deg"].shift(lag_steps).bfill()
            # Suppress pitch shedding
            df.loc[mask, "blade_pitch_deg"] = np.maximum(0.0, pitched_slice - (3.0 * config.severity))

        elif config.fault_type == FaultType.SENSOR_DROPOUT:
            # Introduce NaNs on targeted channel or generator speed
            target = config.channel or "generator_speed_rpm"
            if target in df.columns:
                df.loc[mask, target] = np.nan

        elif config.fault_type == FaultType.SENSOR_FREEZE:
            # Freeze target sensor at its initial value
            target = config.channel or "wind_speed_mps"
            if target in df.columns:
                frozen_val = df.loc[mask, target].iloc[0]
                df.loc[mask, target] = frozen_val

        elif config.fault_type == FaultType.TORQUE_SPIKE:
            # Inject instantaneous high-magnitude torque transient
            spike_mag = 12000.0 * config.severity
            df.loc[mask, "generator_torque_nm"] = df.loc[mask, "generator_torque_nm"] + spike_mag

        elif config.fault_type == FaultType.NOISY_WIND_SENSOR:
            # Inject high frequency zero-mean Gaussian noise on anemometer
            noise = np.random.normal(0.0, 4.0 * config.severity, size=int(mask.sum()))
            df.loc[mask, "wind_speed_mps"] = np.clip(df.loc[mask, "wind_speed_mps"] + noise, 0.0, 45.0)

        elif config.fault_type == FaultType.YAW_MISALIGNMENT:
            # Induce persistent large yaw tracking error
            offset = 14.0 * config.severity
            df.loc[mask, "nacelle_yaw_error"] = df.loc[mask, "nacelle_yaw_error"] + offset

        elif config.fault_type == FaultType.POWER_UNDERPERFORMANCE:
            # Substantial derating / electrical underperformance
            factor = max(0.2, 1.0 - (0.45 * config.severity))
            df.loc[mask, "electrical_power_kw"] = df.loc[mask, "electrical_power_kw"] * factor

        elif config.fault_type == FaultType.TIMESTAMP_GAP:
            # Drop rows within the interior of the window to create sampling discontinuity
            drop_indices = df[mask].index[2:-2]
            df = df.drop(drop_indices).reset_index(drop=True)

        elif config.fault_type == FaultType.CONTROLLER_STATE_FAULT:
            # Force inappropriate illegal state transition (e.g. IDLE during full load)
            df.loc[mask, "controller_state"] = "IDLE"

        return df

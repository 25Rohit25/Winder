"""Domain models for wind turbine telemetry datasets and metadata."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ControllerState(str, Enum):
    """Wind turbine supervisory controller state machine definitions."""

    IDLE = "IDLE"
    STARTUP = "STARTUP"
    BELOW_RATED = "BELOW_RATED"  # Region 2 (optimum tip-speed ratio tracking)
    TRANSITION = "TRANSITION"    # Region 2.5 (approaching rated generator speed)
    RATED_POWER = "RATED_POWER"  # Region 3 (full rated aerodynamic extraction)
    ABOVE_RATED = "ABOVE_RATED"  # Region 3 (full pitch regulation active)
    SHUTDOWN = "SHUTDOWN"
    FAULT_TRIP = "FAULT_TRIP"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class TelemetrySample(BaseModel):
    """Single-instant engineering measurement vector from turbine SCADA/sim."""

    timestamp: float = Field(..., description="Simulation or test time elapsed in seconds")
    wind_speed_mps: float = Field(..., description="Hub-height effective wind speed in m/s")
    rotor_speed_rpm: float = Field(..., description="Low-speed shaft rotor rotational velocity in RPM")
    generator_speed_rpm: float = Field(..., description="High-speed shaft generator velocity in RPM")
    generator_torque_nm: float = Field(..., description="High-speed shaft generator electromagnetic torque in Nm")
    blade_pitch_deg: float = Field(..., description="Collective blade pitch angle in degrees")
    electrical_power_kw: float = Field(..., description="Active 3-phase grid power in kW")
    tower_acceleration: float = Field(..., description="Fore-aft nacelle/tower head acceleration in m/s^2")
    nacelle_yaw_error: float = Field(..., description="Aerodynamic wind vane to nacelle misalignment in degrees")
    controller_state: str = Field(default="BELOW_RATED", description="Supervisory control state")
    fault_flags: int = Field(default=0, description="Active discrete fault alarm bitmask")


class DatasetMetadata(BaseModel):
    """Descriptive metadata and high-level statistics for an ingested telemetry dataset."""

    dataset_id: str
    filename: str
    scenario_type: str = Field(default="normal_run", description="Engineering scenario descriptor")
    sample_count: int
    duration_sec: float
    sampling_rate_hz: float
    time_step_sec: float
    start_time: float
    end_time: float
    columns: List[str]
    summary_stats: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    created_at: str

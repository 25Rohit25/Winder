"""Configuration management for WindCtrl Validate platform."""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field


class TurbineParameters(BaseModel):
    """Reference aerodynamic and electromechanical parameters (NREL 5MW Baseline)."""

    rated_power_kw: float = Field(default=5000.0, description="Rated electrical power in kW")
    cut_in_wind_speed_mps: float = Field(default=3.0, description="Cut-in wind speed in m/s")
    rated_wind_speed_mps: float = Field(default=11.4, description="Rated wind speed in m/s")
    cut_out_wind_speed_mps: float = Field(default=25.0, description="Cut-out wind speed in m/s")

    min_rotor_speed_rpm: float = Field(default=6.9, description="Minimum operational rotor speed in RPM")
    rated_rotor_speed_rpm: float = Field(default=12.1, description="Rated operational rotor speed in RPM")
    max_rotor_speed_rpm: float = Field(default=14.5, description="Maximum continuous operational rotor speed in RPM")
    overspeed_trip_rpm: float = Field(default=15.0, description="Emergency overspeed trip threshold in RPM")

    gearbox_ratio: float = Field(default=97.0, description="Drive train gearbox ratio (rotor to generator)")
    rated_generator_speed_rpm: float = Field(default=1173.7, description="Rated generator speed in RPM (12.1 * 97)")
    rated_generator_torque_nm: float = Field(default=43093.55, description="Rated generator torque in Nm")
    max_generator_torque_nm: float = Field(default=47402.91, description="Peak torque limit (110% of rated) in Nm")

    min_pitch_deg: float = Field(default=0.0, description="Fine pitch angle limit below rated wind in degrees")
    max_pitch_deg: float = Field(default=90.0, description="Full feather pitch angle in degrees")
    max_pitch_rate_dps: float = Field(default=8.0, description="Maximum allowable pitch actuator rate in deg/s")

    max_yaw_error_deg: float = Field(default=10.0, description="Allowable nacelle yaw error threshold in degrees")
    max_tower_accel_mps2: float = Field(default=0.5, description="Fore-aft tower acceleration limit in m/s^2")


class Settings(BaseModel):
    """System-wide application settings."""

    app_name: str = "WindCtrl Validate"
    app_version: str = "1.0.0"
    environment: str = Field(default=os.getenv("WINDCTRL_ENV", "development"))
    debug: bool = Field(default=os.getenv("WINDCTRL_DEBUG", "true").lower() in ("true", "1", "yes"))

    host: str = Field(default=os.getenv("WINDCTRL_HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("WINDCTRL_PORT", "8000")))

    # CORS origins
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # File storage paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
    data_dir: Path = base_dir / "data"
    reports_dir: Path = base_dir / "reports" / "generated"
    templates_dir: Path = base_dir / "reports" / "templates"

    # Turbine specs
    turbine: TurbineParameters = Field(default_factory=TurbineParameters)

    # Tooling
    latex_cmd: str = Field(default=os.getenv("WINDCTRL_LATEX_CMD", "pdflatex"))
    enable_pdf_fallback: bool = Field(default=True)


# Global singleton settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.data_dir / "baseline", exist_ok=True)
os.makedirs(settings.data_dir / "faults", exist_ok=True)
os.makedirs(settings.data_dir / "generated", exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)
os.makedirs(settings.templates_dir, exist_ok=True)

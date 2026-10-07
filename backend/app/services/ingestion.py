"""Signal ingestion, schema validation, and dataset metadata extraction."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Union
import numpy as np
import pandas as pd

from backend.app.core.exceptions import InvalidTelemetryError, SignalIntegrityError
from backend.app.models.dataset import DatasetMetadata

REQUIRED_TELEMETRY_COLUMNS = [
    "timestamp",
    "wind_speed_mps",
    "rotor_speed_rpm",
    "generator_speed_rpm",
    "generator_torque_nm",
    "blade_pitch_deg",
    "electrical_power_kw",
    "tower_acceleration",
    "nacelle_yaw_error",
    "controller_state",
    "fault_flags",
]


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate DataFrame contains all expected turbine telemetry channels."""
    missing = [col for col in REQUIRED_TELEMETRY_COLUMNS if col not in df.columns]
    if missing:
        return False, missing
    return True, []


def load_telemetry_csv(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load telemetry CSV file and enforce column data integrity."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Telemetry file does not exist: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise InvalidTelemetryError(f"Failed to parse CSV file: {exc}") from exc

    is_valid, missing_cols = validate_schema(df)
    if not is_valid:
        raise InvalidTelemetryError(
            f"Telemetry file is missing mandatory channels: {missing_cols}"
        )

    # Ensure numeric types on continuous channels
    numeric_cols = [
        "timestamp",
        "wind_speed_mps",
        "rotor_speed_rpm",
        "generator_speed_rpm",
        "generator_torque_nm",
        "blade_pitch_deg",
        "electrical_power_kw",
        "tower_acceleration",
        "nacelle_yaw_error",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # String controller state & integer bitmask
    df["controller_state"] = df["controller_state"].astype(str)
    df["fault_flags"] = pd.to_numeric(df["fault_flags"], errors="coerce").fillna(0).astype(int)

    return df


def compute_dataset_metadata(
    df: pd.DataFrame,
    filename: str,
    dataset_id: str,
    scenario_type: str = "operational",
) -> DatasetMetadata:
    """Derive summary statistical metadata and timing characteristics."""
    if df.empty:
        raise SignalIntegrityError("Cannot generate metadata for empty dataframe")

    time_col = df["timestamp"].dropna()
    if len(time_col) < 2:
        raise SignalIntegrityError("Telemetry dataset requires at least 2 timestamped samples")

    t_start = float(time_col.iloc[0])
    t_end = float(time_col.iloc[-1])
    duration = float(t_end - t_start)
    dt_series = time_col.diff().dropna()
    dt_mean = float(dt_series.mean()) if not dt_series.empty else 0.05
    sampling_rate = float(1.0 / dt_mean) if dt_mean > 0 else 0.0

    numeric_cols = [c for c in REQUIRED_TELEMETRY_COLUMNS if c not in ("controller_state", "fault_flags")]
    summary_stats = {}
    for col in numeric_cols:
        s = df[col].dropna()
        if not s.empty:
            summary_stats[col] = {
                "min": float(s.min()),
                "max": float(s.max()),
                "mean": float(s.mean()),
                "std": float(s.std()) if len(s) > 1 else 0.0,
            }
        else:
            summary_stats[col] = {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}

    return DatasetMetadata(
        dataset_id=dataset_id,
        filename=filename,
        scenario_type=scenario_type,
        sample_count=len(df),
        duration_sec=duration,
        sampling_rate_hz=round(sampling_rate, 2),
        time_step_sec=round(dt_mean, 4),
        start_time=t_start,
        end_time=t_end,
        columns=list(df.columns),
        summary_stats=summary_stats,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def save_telemetry_csv(df: pd.DataFrame, target_path: Union[str, Path]) -> None:
    """Save cleaned or synthesized telemetry to CSV."""
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

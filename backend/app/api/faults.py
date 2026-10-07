"""Fault injection simulation API endpoints."""

import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.models.dataset import DatasetMetadata
from backend.app.services.fault_injection import FaultConfig, FaultInjectionEngine, FaultType
from backend.app.services.ingestion import (
    compute_dataset_metadata,
    load_telemetry_csv,
    save_telemetry_csv,
)

router = APIRouter(prefix="/faults", tags=["Fault Injection"])


class FaultInjectionRequest(BaseModel):
    """Specification of fault to be synthetically introduced."""

    base_dataset: str = Field(default="normal_run.csv", description="Source baseline dataset file")
    fault_type: FaultType = Field(default=FaultType.ROTOR_OVERSPEED)
    start_time: float = Field(default=20.0, description="Start time in seconds")
    duration: float = Field(default=10.0, description="Fault duration in seconds")
    severity: float = Field(default=1.0, ge=0.1, le=5.0, description="Magnitude multiplier")
    channel: str = Field(default="rotor_speed_rpm", description="Channel targeted by fault")


@router.post("/inject", response_model=DatasetMetadata)
def inject_fault(request: FaultInjectionRequest):
    """Inject synthetic fault into baseline telemetry and save resulting dataset."""
    found_path = None
    for sub in ["baseline", "faults", "generated"]:
        candidate = settings.data_dir / sub / request.base_dataset
        if candidate.exists():
            found_path = candidate
            break

    if not found_path:
        raise HTTPException(
            status_code=404,
            detail=f"Base dataset '{request.base_dataset}' not found.",
        )

    df_base = load_telemetry_csv(found_path)
    cfg = FaultConfig(
        fault_type=request.fault_type,
        start_time=request.start_time,
        duration=request.duration,
        severity=request.severity,
        channel=request.channel,
    )

    df_faulted = FaultInjectionEngine.inject_fault(df_base, cfg)

    # Save to generated directory
    tag = f"synth_{request.fault_type.value.lower()}_{uuid.uuid4().hex[:6]}"
    out_filename = f"{tag}.csv"
    out_path = settings.data_dir / "generated" / out_filename
    save_telemetry_csv(df_faulted, out_path)

    meta = compute_dataset_metadata(
        df_faulted,
        filename=out_filename,
        dataset_id=tag,
        scenario_type=f"fault_{request.fault_type.value.lower()}",
    )
    return meta

"""Controller validation execution endpoints."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.runs import register_run
from backend.app.core.config import settings
from backend.app.models.validation import ValidationRunSummary
from backend.app.services.controller_validator import ControllerValidationEngine
from backend.app.services.ingestion import load_telemetry_csv

router = APIRouter(prefix="/validation", tags=["Validation Execution"])


class ValidationRunRequest(BaseModel):
    """Execution request specification."""

    dataset_name: str = Field(default="normal_run.csv", description="Target dataset file name")
    scenario_type: Optional[str] = Field(default=None, description="Optional scenario label")
    run_id: Optional[str] = Field(default=None, description="Optional custom run ID")


@router.post("/run", response_model=ValidationRunSummary)
def execute_validation(request: ValidationRunRequest):
    """Execute full battery of validation rules on specified dataset."""
    found_path = None
    for sub in ["baseline", "faults", "generated"]:
        candidate = settings.data_dir / sub / request.dataset_name
        if candidate.exists():
            found_path = candidate
            break

    if not found_path:
        raise HTTPException(
            status_code=404,
            detail=f"Target dataset '{request.dataset_name}' does not exist in data repository.",
        )

    df = load_telemetry_csv(found_path)
    engine = ControllerValidationEngine(run_id=request.run_id)
    scenario_type = request.scenario_type or Path(request.dataset_name).stem

    summary = engine.run_validation(
        df,
        dataset_name=request.dataset_name,
        scenario_type=scenario_type,
    )
    register_run(summary)
    return summary

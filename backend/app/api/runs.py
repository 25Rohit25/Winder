"""Validation run history repository and lookup endpoints."""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException

from backend.app.models.validation import ValidationRunSummary

router = APIRouter(prefix="/validation/runs", tags=["Validation Runs"])

# Global run cache registry
RUN_STORE: Dict[str, ValidationRunSummary] = {}


def register_run(summary: ValidationRunSummary) -> None:
    """Store run summary into cache registry."""
    RUN_STORE[summary.run_id] = summary


@router.get("", response_model=List[ValidationRunSummary])
def list_validation_runs():
    """Retrieve history of all executed validation runs."""
    return list(reversed(list(RUN_STORE.values())))


@router.get("/{run_id}", response_model=ValidationRunSummary)
def get_validation_run(run_id: str):
    """Retrieve detailed validation evidence and results for a specific run ID."""
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail=f"Validation run '{run_id}' not found.")
    return RUN_STORE[run_id]

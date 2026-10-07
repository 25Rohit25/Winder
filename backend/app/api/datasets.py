"""Dataset catalog, upload handler, and telemetry streaming endpoints."""

import os
from pathlib import Path
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from backend.app.core.config import settings
from backend.app.models.dataset import DatasetMetadata
from backend.app.services.ingestion import (
    compute_dataset_metadata,
    load_telemetry_csv,
    validate_schema,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=List[DatasetMetadata])
def list_datasets():
    """List all available baseline, fault, and generated turbine telemetry datasets."""
    datasets: List[DatasetMetadata] = []
    search_dirs = [
        ("baseline", settings.data_dir / "baseline"),
        ("fault", settings.data_dir / "faults"),
        ("generated", settings.data_dir / "generated"),
    ]

    for scenario_cat, directory in search_dirs:
        if directory.exists():
            for f in directory.glob("*.csv"):
                try:
                    df = pd.read_csv(f)
                    meta = compute_dataset_metadata(
                        df,
                        filename=f.name,
                        dataset_id=f"{scenario_cat}_{f.stem}",
                        scenario_type=f.stem,
                    )
                    datasets.append(meta)
                except Exception:
                    continue

    return datasets


@router.post("/upload", response_model=DatasetMetadata)
async def upload_dataset(file: UploadFile = File(...)):
    """Upload new SCADA or simulation telemetry CSV dataset."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV telemetry files are supported.")

    target_dir = settings.data_dir / "generated"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file.filename

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    try:
        df = load_telemetry_csv(target_path)
    except Exception as exc:
        if target_path.exists():
            os.remove(target_path)
        raise HTTPException(status_code=422, detail=f"Invalid telemetry format: {exc}")

    meta = compute_dataset_metadata(
        df,
        filename=file.filename,
        dataset_id=f"gen_{Path(file.filename).stem}",
        scenario_type="uploaded_test",
    )
    return meta


@router.get("/{filename}/telemetry")
def get_dataset_telemetry(
    filename: str,
    downsample: Optional[int] = Query(default=1, ge=1, le=20, description="Downsample stride factor"),
):
    """Retrieve full or downsampled channel time-series vector for plotting."""
    # Look in baseline, faults, then generated
    found_path = None
    for sub in ["baseline", "faults", "generated"]:
        candidate = settings.data_dir / sub / filename
        if candidate.exists():
            found_path = candidate
            break

    if not found_path:
        raise HTTPException(status_code=404, detail=f"Dataset '{filename}' not found.")

    df = pd.read_csv(found_path)
    if downsample > 1:
        df = df.iloc[::downsample].reset_index(drop=True)

    # Return records as JSON
    return {
        "filename": filename,
        "sample_count": len(df),
        "columns": list(df.columns),
        "data": df.to_dict(orient="records"),
    }

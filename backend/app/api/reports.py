"""Report generation and document download endpoints."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.api.runs import RUN_STORE
from backend.app.core.config import settings
from backend.app.models.report import ReportConfig, ReportMetadata
from backend.app.services.ingestion import load_telemetry_csv
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])
report_service = ReportService()


@router.get("/{run_id}", response_model=ReportMetadata)
def get_or_generate_report(run_id: str):
    """Retrieve existing or dynamically compile certification report for given run ID."""
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail=f"Validation run '{run_id}' not found.")

    summary = RUN_STORE[run_id]

    # Look for telemetry data to attach plot
    telemetry_df = None
    for sub in ["baseline", "faults", "generated"]:
        candidate = settings.data_dir / sub / summary.dataset_name
        if candidate.exists():
            try:
                telemetry_df = load_telemetry_csv(candidate)
            except Exception:
                pass
            break

    metadata = report_service.generate_report(summary, telemetry_df=telemetry_df)
    return metadata


@router.get("/{run_id}/pdf")
def download_pdf(run_id: str):
    """Download compiled PDF validation certificate."""
    pdf_path = settings.reports_dir / run_id / f"validation_report_{run_id}.pdf"
    if not pdf_path.exists():
        # Try generating it
        if run_id in RUN_STORE:
            get_or_generate_report(run_id)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF report for '{run_id}' not found.")

    return FileResponse(
        path=str(pdf_path),
        filename=f"WindTurbine_Validation_Report_{run_id}.pdf",
        media_type="application/pdf",
    )


@router.get("/{run_id}/tex")
def download_tex(run_id: str):
    """Download LaTeX source .tex file for audit archive."""
    tex_path = settings.reports_dir / run_id / f"validation_report_{run_id}.tex"
    if not tex_path.exists():
        if run_id in RUN_STORE:
            get_or_generate_report(run_id)
        if not tex_path.exists():
            raise HTTPException(status_code=404, detail=f"LaTeX source for '{run_id}' not found.")

    return FileResponse(
        path=str(tex_path),
        filename=f"validation_report_{run_id}.tex",
        media_type="application/x-tex",
    )

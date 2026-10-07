"""System health, readiness probes, and runtime diagnostic endpoints."""

import sys
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("")
def get_health():
    """Return health status, environment, and system diagnostics."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "turbine_model": "NREL 5MW Baseline (IEC Class IB)",
        "diagnostics": {
            "baseline_datasets_ready": (settings.data_dir / "baseline").exists(),
            "fault_datasets_ready": (settings.data_dir / "faults").exists(),
            "pdf_fallback_enabled": settings.enable_pdf_fallback,
        },
    }

"""API route registry for WindCtrl Validate platform."""

from fastapi import APIRouter

from backend.app.api.datasets import router as datasets_router
from backend.app.api.faults import router as faults_router
from backend.app.api.health import router as health_router
from backend.app.api.reports import router as reports_router
from backend.app.api.runs import router as runs_router
from backend.app.api.validation import router as validation_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(datasets_router)
api_router.include_router(validation_router)
api_router.include_router(runs_router)
api_router.include_router(faults_router)
api_router.include_router(reports_router)

__all__ = ["api_router"]

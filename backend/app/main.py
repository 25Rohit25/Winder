"""Main entry point for WindCtrl Validate FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api import api_router
from backend.app.api.runs import register_run
from backend.app.core.config import settings
from backend.app.core.exceptions import WindCtrlException
from backend.app.core.logging import setup_logger
from backend.app.services.controller_validator import ControllerValidationEngine

logger = setup_logger("windctrl.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager preloading baseline validation runs for immediate UI demo."""
    logger.info("Initializing WindCtrl Validate service...")

    # Pre-populate baseline runs if data files exist
    baseline_norm = settings.data_dir / "baseline" / "normal_run.csv"
    fault_ov = settings.data_dir / "faults" / "overspeed_fault.csv"

    if baseline_norm.exists():
        try:
            eng = ControllerValidationEngine(run_id="run-baseline-001")
            summary = eng.run_validation(baseline_norm, dataset_name="normal_run.csv", scenario_type="normal_run")
            register_run(summary)
            logger.info("Pre-loaded baseline normal_run validation into registry.")
        except Exception as e:
            logger.warning(f"Failed to preload baseline run: {e}")

    if fault_ov.exists():
        try:
            eng = ControllerValidationEngine(run_id="run-fault-ov-002")
            summary_f = eng.run_validation(fault_ov, dataset_name="overspeed_fault.csv", scenario_type="overspeed_fault")
            register_run(summary_f)
            logger.info("Pre-loaded overspeed fault run into registry.")
        except Exception as e:
            logger.warning(f"Failed to preload fault run: {e}")

    yield
    logger.info("Shutting down WindCtrl Validate service.")


app = FastAPI(
    title="WindCtrl Validate",
    description=(
        "Wind Turbine Controller Validation & Automated Reporting Toolkit. "
        "Automated supervisory control rule verification, fault injection, and IEC 61400 reporting."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local engineering dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WindCtrlException)
async def windctrl_exception_handler(request: Request, exc: WindCtrlException):
    """Structured handler for domain-specific errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error_type": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


# Attach API router
app.include_router(api_router)


@app.get("/")
def root():
    """Root platform discovery endpoint."""
    return {
        "platform": "WindCtrl Validate",
        "description": "Wind Turbine Controller Validation & Automated Reporting Toolkit",
        "version": settings.app_version,
        "docs_url": "/docs",
        "api_v1": "/api/v1",
        "health": "/api/v1/health",
        "turbine_model": "NREL 5MW Baseline Wind Turbine",
    }

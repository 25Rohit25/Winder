"""End-to-end integration tests for ControllerValidationEngine pipeline."""

from pathlib import Path
import pytest

from backend.app.core.config import settings
from backend.app.models.validation import ValidationRunSummary, ValidationStatus
from backend.app.services.controller_validator import ControllerValidationEngine


def test_validation_engine_normal_run_pipeline():
    """Verify entire pipeline executes cleanly on the baseline normal_run dataset."""
    dataset_path = settings.data_dir / "baseline" / "normal_run.csv"
    assert dataset_path.exists(), f"Missing dataset: {dataset_path}"

    engine = ControllerValidationEngine(run_id="test-integration-001")
    summary = engine.run_validation(dataset_path, dataset_name="normal_run.csv", scenario_type="normal_run")

    assert isinstance(summary, ValidationRunSummary)
    assert summary.run_id == "test-integration-001"
    assert summary.total_tests >= 12
    assert summary.failed_count == 0, f"Normal run should have zero failures, got {summary.failed_count}"
    assert summary.overall_status == ValidationStatus.PASS
    assert summary.validation_score >= 90.0
    assert summary.signal_completeness_pct == 100.0
    assert summary.execution_duration_ms > 0.0
    assert len(summary.results) == summary.total_tests


def test_validation_engine_gust_event_pipeline():
    """Verify entire pipeline on dynamic gust_event dataset."""
    dataset_path = settings.data_dir / "baseline" / "gust_event.csv"
    assert dataset_path.exists()

    engine = ControllerValidationEngine(run_id="test-integration-002")
    summary = engine.run_validation(dataset_path, dataset_name="gust_event.csv", scenario_type="gust_event")

    assert isinstance(summary, ValidationRunSummary)
    assert summary.total_tests >= 12
    assert summary.failed_count == 0
    assert summary.overall_status in (ValidationStatus.PASS, ValidationStatus.WARNING)
    assert summary.validation_score >= 80.0

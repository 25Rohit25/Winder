"""Regression test suite proving deterministic detection of all injected fault scenarios."""

from pathlib import Path
import pytest

from backend.app.core.config import settings
from backend.app.models.validation import ValidationStatus
from backend.app.services.controller_validator import ControllerValidationEngine


@pytest.fixture(scope="module")
def validation_engine() -> ControllerValidationEngine:
    return ControllerValidationEngine()


def test_regression_normal_run_clean_verdict(validation_engine: ControllerValidationEngine):
    """Regression benchmark: Normal run must pass with 0 failures and score >= 90."""
    path = settings.data_dir / "baseline" / "normal_run.csv"
    summary = validation_engine.run_validation(path, dataset_name="normal_run.csv")

    assert summary.overall_status == ValidationStatus.PASS
    assert summary.failed_count == 0
    assert summary.validation_score >= 90.0


def test_regression_overspeed_fault_detected(validation_engine: ControllerValidationEngine):
    """Regression benchmark: Overspeed fault MUST be caught by overspeed validator."""
    path = settings.data_dir / "faults" / "overspeed_fault.csv"
    summary = validation_engine.run_validation(path, dataset_name="overspeed_fault.csv")

    assert summary.overall_status == ValidationStatus.FAIL
    assert summary.failed_count >= 1
    # Check that overspeed validator caught the breach
    overspeed_fails = [
        r for r in summary.results
        if r.status == ValidationStatus.FAIL and "overspeed" in r.validator
    ]
    assert len(overspeed_fails) > 0, "Failed to catch injected overspeed trip fault!"


def test_regression_sensor_dropout_detected(validation_engine: ControllerValidationEngine):
    """Regression benchmark: NaN generator speed dropout MUST be caught by signal integrity."""
    path = settings.data_dir / "faults" / "sensor_dropout.csv"
    summary = validation_engine.run_validation(path, dataset_name="sensor_dropout.csv")

    assert summary.overall_status == ValidationStatus.FAIL
    nan_fails = [
        r for r in summary.results
        if r.status == ValidationStatus.FAIL and "signal_integrity.nan_dropout" in r.validator
    ]
    assert len(nan_fails) > 0, "Failed to catch injected sensor dropout NaNs!"


def test_regression_torque_spike_detected(validation_engine: ControllerValidationEngine):
    """Regression benchmark: Sudden converter torque transient MUST trigger torque spike alarm."""
    path = settings.data_dir / "faults" / "torque_spike.csv"
    summary = validation_engine.run_validation(path, dataset_name="torque_spike.csv")

    assert summary.overall_status == ValidationStatus.FAIL
    torque_alarms = [
        r for r in summary.results
        if r.status == ValidationStatus.FAIL and "torque_control" in r.validator
    ]
    assert len(torque_alarms) > 0, "Failed to catch injected torque transient spike!"


def test_regression_yaw_error_fault_detected(validation_engine: ControllerValidationEngine):
    """Regression benchmark: Nacelle misorientation MUST be caught by yaw validator."""
    path = settings.data_dir / "faults" / "yaw_error_fault.csv"
    summary = validation_engine.run_validation(path, dataset_name="yaw_error_fault.csv")

    assert summary.overall_status == ValidationStatus.FAIL
    yaw_fails = [
        r for r in summary.results
        if r.status == ValidationStatus.FAIL and "yaw" in r.validator
    ]
    assert len(yaw_fails) > 0, "Failed to catch injected yaw misalignment fault!"

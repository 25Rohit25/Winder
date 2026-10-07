"""Validation engine orchestrator coordinating all domain rules and aggregating evidence."""

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union
import pandas as pd

from backend.app.core.exceptions import ValidationExecutionError
from backend.app.core.logging import setup_logger
from backend.app.models.validation import (
    ValidationEvidence,
    ValidationRunSummary,
    ValidationStatus,
)
from backend.app.services.ingestion import load_telemetry_csv
from backend.app.services.metrics import calculate_run_metrics, compute_validation_score
from backend.app.validators import (
    ControllerStateValidator,
    OverspeedValidator,
    PitchControlValidator,
    PowerCurveValidator,
    RotorSpeedValidator,
    SignalIntegrityValidator,
    TorqueControlValidator,
    YawValidator,
)


class ControllerValidationEngine:
    """Master orchestrator executing the full battery of turbine controller verification checks."""

    def __init__(self, run_id: Optional[str] = None) -> None:
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        self.logger = setup_logger("windctrl.engine", run_id=self.run_id)

        # Instantiate modular validators
        self.signal_validator = SignalIntegrityValidator()
        self.rotor_validator = RotorSpeedValidator()
        self.overspeed_validator = OverspeedValidator()
        self.pitch_validator = PitchControlValidator()
        self.torque_validator = TorqueControlValidator()
        self.power_validator = PowerCurveValidator()
        self.yaw_validator = YawValidator()
        self.state_validator = ControllerStateValidator()

    def run_validation(
        self,
        data: Union[pd.DataFrame, str, Path],
        dataset_name: str = "dataset.csv",
        scenario_type: str = "operational",
    ) -> ValidationRunSummary:
        """Execute all validation rules across the telemetry input and return structured run summary."""
        t_start = time.perf_counter()
        self.logger.info(f"Starting validation run {self.run_id} on {dataset_name} ({scenario_type})")

        # Load data if path passed
        if isinstance(data, (str, Path)):
            df = load_telemetry_csv(data)
            dataset_name = Path(data).name
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValidationExecutionError(f"Unsupported data type for validation: {type(data)}")

        evidences: List[ValidationEvidence] = []

        try:
            # 1. Signal Integrity (Prerequisite)
            sig_results = self.signal_validator.validate(df)
            evidences.extend(sig_results)

            # Check if dataset was completely empty or failed critically
            crit_fails = [e for e in sig_results if e.status == ValidationStatus.FAIL and e.severity == "CRITICAL"]
            if not crit_fails:
                # 2. Rotor Speed & Kinematics
                evidences.extend(self.rotor_validator.validate(df))

                # 3. Overspeed Protection
                evidences.extend(self.overspeed_validator.validate(df))

                # 4. Aerodynamic Pitch Control
                evidences.extend(self.pitch_validator.validate(df))

                # 5. Generator Torque Dynamics
                evidences.extend(self.torque_validator.validate(df))

                # 6. Power Curve & Energy Yield
                evidences.extend(self.power_validator.validate(df))

                # 7. Yaw Alignment & Tracking
                evidences.extend(self.yaw_validator.validate(df))

                # 8. Controller State Machine
                evidences.extend(self.state_validator.validate(df))

        except Exception as exc:
            self.logger.error(f"Internal error during validation execution: {exc}")
            raise ValidationExecutionError(f"Validation engine failure: {exc}") from exc

        exec_duration_ms = (time.perf_counter() - t_start) * 1000.0

        # Compute counts
        total_tests = len(evidences)
        passed_count = sum(1 for e in evidences if e.status == ValidationStatus.PASS)
        warning_count = sum(1 for e in evidences if e.status == ValidationStatus.WARNING)
        failed_count = sum(1 for e in evidences if e.status == ValidationStatus.FAIL)

        # Overall Status
        if failed_count > 0:
            overall_status = ValidationStatus.FAIL
        elif warning_count > 0:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASS

        # Calculate metrics & score
        score = compute_validation_score(passed_count, warning_count, failed_count, total_tests)
        metrics = calculate_run_metrics(df, evidences)

        summary = ValidationRunSummary(
            run_id=self.run_id,
            dataset_name=dataset_name,
            scenario_type=scenario_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_status=overall_status,
            validation_score=score,
            total_tests=total_tests,
            passed_count=passed_count,
            warning_count=warning_count,
            failed_count=failed_count,
            detection_rate_pct=metrics["detection_rate_pct"],
            false_positive_rate_pct=metrics["false_positive_rate_pct"],
            max_rotor_speed_rpm=metrics["max_rotor_speed_rpm"],
            max_generator_torque_nm=metrics["max_generator_torque_nm"],
            max_electrical_power_kw=metrics["max_electrical_power_kw"],
            max_power_deviation_pct=metrics["max_power_deviation_pct"],
            pitch_response_time_sec=metrics["pitch_response_time_sec"],
            max_yaw_error_deg=metrics["max_yaw_error_deg"],
            signal_completeness_pct=metrics["signal_completeness_pct"],
            execution_duration_ms=round(exec_duration_ms, 2),
            results=evidences,
        )

        self.logger.info(
            f"Validation run {self.run_id} completed in {exec_duration_ms:.1f}ms: "
            f"{overall_status.value} (Score: {score:.1f}, Pass: {passed_count}, Warn: {warning_count}, Fail: {failed_count})"
        )
        return summary

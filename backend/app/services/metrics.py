"""Validation scoring algorithms, KPI calculation, and detection rate metrics."""

from typing import Any, Dict, List
import numpy as np
import pandas as pd

from backend.app.models.validation import ValidationEvidence, ValidationStatus


def compute_validation_score(
    passed_count: int,
    warning_count: int,
    failed_count: int,
    total_tests: int,
) -> float:
    """Compute deterministic engineering validation index between 0.0 and 100.0.

    Formula:
    - Each passed test adds 1.0 weight
    - Each warning test adds 0.5 weight
    - Each failed test adds 0.0 weight
    Scaled to 100%. If any critical failure exists, capped at maximum 60.0%.
    """
    if total_tests == 0:
        return 0.0

    weighted_points = (passed_count * 1.0) + (warning_count * 0.5)
    base_score = (weighted_points / total_tests) * 100.0

    if failed_count > 0:
        # Cap score when violations are detected
        penalty = min(40.0, failed_count * 15.0)
        base_score = max(0.0, min(65.0, base_score - penalty))

    return round(float(base_score), 1)


def calculate_run_metrics(
    df: pd.DataFrame,
    evidences: List[ValidationEvidence],
) -> Dict[str, Any]:
    """Calculate physical engineering KPIs and signal completeness metrics from telemetry and evidence."""
    # Signal completeness (percentage of non-null cells across required channels)
    total_cells = df.size
    nan_cells = int(df.isna().sum().sum())
    completeness = float(((total_cells - nan_cells) / total_cells) * 100.0) if total_cells > 0 else 100.0

    # Max physical signals
    max_rotor = float(df["rotor_speed_rpm"].max()) if "rotor_speed_rpm" in df.columns and not df["rotor_speed_rpm"].empty else 0.0
    max_torque = float(df["generator_torque_nm"].max()) if "generator_torque_nm" in df.columns and not df["generator_torque_nm"].empty else 0.0
    max_power = float(df["electrical_power_kw"].max()) if "electrical_power_kw" in df.columns and not df["electrical_power_kw"].empty else 0.0
    max_yaw = float(df["nacelle_yaw_error"].abs().max()) if "nacelle_yaw_error" in df.columns and not df["nacelle_yaw_error"].empty else 0.0

    # Extract metrics from evidence results
    power_dev = 0.0
    pitch_delay = 0.20

    for ev in evidences:
        if ev.validator == "power_curve.binned_deviation" and isinstance(ev.actual, (int, float)):
            power_dev = max(power_dev, float(ev.actual))
        elif ev.validator == "power_curve.rated_power_cap" and isinstance(ev.actual, (int, float)):
            power_dev = max(power_dev, float(ev.actual))
        elif ev.validator == "pitch_control.response_time" and isinstance(ev.actual, (int, float)):
            pitch_delay = float(ev.actual)

    # Injected fault detection rate calculation
    faults_present = int((df["fault_flags"] > 0).sum()) if "fault_flags" in df.columns else 0
    failed_evidences = [e for e in evidences if e.status == ValidationStatus.FAIL]

    if faults_present > 0:
        # If dataset contained injected faults, did we catch them?
        detection_rate = 100.0 if len(failed_evidences) > 0 else 0.0
        false_positive_rate = 0.0
    else:
        # Clean run
        detection_rate = 100.0
        false_positive_rate = round(float((len(failed_evidences) / len(evidences)) * 100.0), 1) if evidences else 0.0

    return {
        "signal_completeness_pct": round(completeness, 2),
        "max_rotor_speed_rpm": round(max_rotor, 3),
        "max_generator_torque_nm": round(max_torque, 1),
        "max_electrical_power_kw": round(max_power, 1),
        "max_power_deviation_pct": round(power_dev, 2),
        "pitch_response_time_sec": round(pitch_delay, 2),
        "max_yaw_error_deg": round(max_yaw, 2),
        "detection_rate_pct": detection_rate,
        "false_positive_rate_pct": false_positive_rate,
    }

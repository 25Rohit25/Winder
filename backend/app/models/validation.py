"""Domain models for validation results, rules, and run summaries."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Validation rule verdict status."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class ValidationEvidence(BaseModel):
    """Structured engineering evidence emitted by a validation rule."""

    validator: str = Field(..., description="Unique identifier of the executing validator")
    status: ValidationStatus = Field(..., description="Verdict status: PASS, WARNING, or FAIL")
    metric: str = Field(..., description="Physical or algorithmic metric under test")
    actual: Union[float, int, str, None] = Field(..., description="Observed measurement value")
    threshold: Union[float, int, str, None] = Field(..., description="Acceptance threshold or range")
    message: str = Field(..., description="Human-readable engineering diagnostic message")
    timestamp_range: Optional[List[float]] = Field(
        default=None,
        description="Optional [t_start, t_end] window where anomaly occurred",
    )
    severity: str = Field(default="MEDIUM", description="Engineering criticality: LOW, MEDIUM, HIGH, CRITICAL")
    details: Dict[str, Any] = Field(default_factory=dict, description="Supplementary diagnostic telemetry")


class ValidationRunSummary(BaseModel):
    """Holistic summary of an automated validation run over a dataset."""

    run_id: str
    dataset_name: str
    scenario_type: str = "operational"
    timestamp: str
    overall_status: ValidationStatus
    validation_score: float = Field(..., ge=0.0, le=100.0, description="Overall health score (0-100)")

    total_tests: int
    passed_count: int
    warning_count: int
    failed_count: int

    detection_rate_pct: float = Field(default=100.0, description="Fault detection rate percentage")
    false_positive_rate_pct: float = Field(default=0.0, description="Clean-run false alarm rate percentage")

    # Key Engineering Physical KPIs
    max_rotor_speed_rpm: float
    max_generator_torque_nm: float
    max_electrical_power_kw: float
    max_power_deviation_pct: float
    pitch_response_time_sec: float
    max_yaw_error_deg: float
    signal_completeness_pct: float
    execution_duration_ms: float

    # Detailed test-by-test results
    results: List[ValidationEvidence] = Field(default_factory=list)

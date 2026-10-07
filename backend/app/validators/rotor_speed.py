"""Rotor rotational velocity bounds, angular acceleration, and gearbox ratio validation."""

from typing import List, Optional
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus
from backend.app.utils.math_helpers import compute_rate_of_change


class RotorSpeedValidator:
    """Validates low-speed shaft kinematics against aero-elastic structural design limits."""

    def __init__(
        self,
        min_rpm: Optional[float] = None,
        max_operational_rpm: Optional[float] = None,
        max_accel_rpm_s: float = 1.5,
        gearbox_ratio: Optional[float] = None,
    ) -> None:
        self.min_rpm = min_rpm or settings.turbine.min_rotor_speed_rpm
        self.max_operational_rpm = max_operational_rpm or settings.turbine.max_rotor_speed_rpm
        self.max_accel_rpm_s = max_accel_rpm_s
        self.gearbox_ratio = gearbox_ratio or settings.turbine.gearbox_ratio

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Validate operational rotor speed range, acceleration rate-of-change, and drivetrain gearing."""
        results: List[ValidationEvidence] = []
        if df.empty or "rotor_speed_rpm" not in df.columns:
            return results

        # 1. Operational Range Limits (Active Power Production)
        results.append(self._validate_operating_range(df))

        # 2. Angular Acceleration / Rate of Change Limits
        results.append(self._validate_rate_of_change(df))

        # 3. Drivetrain Gearbox Tracking Ratio
        if "generator_speed_rpm" in df.columns:
            results.append(self._validate_gearbox_ratio(df))

        return results

    def _validate_operating_range(self, df: pd.DataFrame) -> ValidationEvidence:
        # Evaluate primarily during operational generating states
        active_mask = ~df["controller_state"].isin(["IDLE", "SHUTDOWN", "STARTUP", "FAULT_TRIP"])
        active_df = df[active_mask] if active_mask.any() else df

        speed = active_df["rotor_speed_rpm"].dropna()
        if speed.empty:
            return ValidationEvidence(
                validator="rotor_speed.operating_range",
                status=ValidationStatus.PASS,
                metric="max_rotor_speed_rpm",
                actual=0.0,
                threshold=f"[{self.min_rpm}, {self.max_operational_rpm}]",
                message="No operational samples to evaluate for rotor speed range.",
            )

        max_val = float(speed.max())
        min_val = float(speed.min())

        under_count = int((speed < self.min_rpm).sum())
        over_count = int((speed > self.max_operational_rpm).sum())

        if under_count == 0 and over_count == 0:
            status = ValidationStatus.PASS
            msg = (
                f"Rotor speed strictly within nominal envelope [{self.min_rpm:.1f}, "
                f"{self.max_operational_rpm:.1f}] RPM (min: {min_val:.2f}, max: {max_val:.2f})."
            )
        elif over_count > 0:
            status = ValidationStatus.WARNING if max_val <= (self.max_operational_rpm + 0.5) else ValidationStatus.FAIL
            msg = (
                f"Rotor speed exceeded maximum operational ceiling: max {max_val:.2f} RPM > "
                f"{self.max_operational_rpm:.1f} RPM ({over_count} samples)."
            )
        else:
            status = ValidationStatus.WARNING
            msg = f"Rotor speed dipped below cut-in operating speed: min {min_val:.2f} RPM < {self.min_rpm:.1f} RPM."

        return ValidationEvidence(
            validator="rotor_speed.operating_range",
            status=status,
            metric="max_rotor_speed_rpm",
            actual=round(max_val, 3),
            threshold=f"[{self.min_rpm:.1f}, {self.max_operational_rpm:.1f}]",
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"min_rpm_observed": round(min_val, 3), "violations_over": over_count, "violations_under": under_count},
        )

    def _validate_rate_of_change(self, df: pd.DataFrame) -> ValidationEvidence:
        time = df["timestamp"]
        speed = df["rotor_speed_rpm"]
        accel = compute_rate_of_change(speed, time).abs()

        max_accel = float(accel.max()) if not accel.empty else 0.0
        violations = int((accel > self.max_accel_rpm_s).sum())

        if violations == 0:
            status = ValidationStatus.PASS
            msg = f"Rotor acceleration dynamics smooth. Max |d(omega)/dt| = {max_accel:.3f} RPM/s <= {self.max_accel_rpm_s} RPM/s."
        elif violations < 5:
            status = ValidationStatus.WARNING
            msg = f"Transient rotor acceleration spike: {max_accel:.3f} RPM/s exceeds limit {self.max_accel_rpm_s} RPM/s ({violations} points)."
        else:
            status = ValidationStatus.FAIL
            msg = f"Excessive rotor angular jerk detected: max rate {max_accel:.3f} RPM/s across {violations} timesteps."

        return ValidationEvidence(
            validator="rotor_speed.rate_of_change",
            status=status,
            metric="max_rotor_acceleration_rpm_s",
            actual=round(max_accel, 3),
            threshold=round(self.max_accel_rpm_s, 2),
            message=msg,
            severity="MEDIUM" if status == ValidationStatus.WARNING else ("HIGH" if status == ValidationStatus.FAIL else "LOW"),
            details={"violations_count": violations},
        )

    def _validate_gearbox_ratio(self, df: pd.DataFrame) -> ValidationEvidence:
        valid_mask = (df["rotor_speed_rpm"] > 1.0) & (df["generator_speed_rpm"] > 50.0)
        subset = df[valid_mask]
        if subset.empty:
            return ValidationEvidence(
                validator="rotor_speed.gearbox_ratio",
                status=ValidationStatus.PASS,
                metric="gearbox_ratio_error_pct",
                actual=0.0,
                threshold=2.0,
                message="Turbine speed below engagement threshold; gearbox ratio check bypassed.",
            )

        ratio_series = subset["generator_speed_rpm"] / subset["rotor_speed_rpm"]
        ratio_err_pct = ((ratio_series - self.gearbox_ratio).abs() / self.gearbox_ratio) * 100.0
        max_err = float(ratio_err_pct.max())

        status = ValidationStatus.PASS if max_err <= 2.5 else ValidationStatus.FAIL
        msg = (
            f"Drivetrain kinematic coupling verified. Gearbox ratio conforms to {self.gearbox_ratio:.1f} (max error {max_err:.2f}%)."
            if status == ValidationStatus.PASS
            else f"Drivetrain slip or sensor disagreement detected: ratio mismatch {max_err:.2f}% exceeds 2.5% tolerance."
        )

        return ValidationEvidence(
            validator="rotor_speed.gearbox_ratio",
            status=status,
            metric="gearbox_ratio_error_pct",
            actual=round(max_err, 2),
            threshold=2.5,
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
        )

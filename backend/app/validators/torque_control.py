"""High-speed shaft generator torque regulation, torque spikes, and limit validator."""

from typing import List, Optional
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus
from backend.app.utils.math_helpers import compute_rate_of_change


class TorqueControlValidator:
    """Validates electromagnetic generator torque demands and converter dynamics."""

    def __init__(
        self,
        rated_torque_nm: Optional[float] = None,
        max_torque_nm: Optional[float] = None,
        max_torque_rate_nm_s: float = 15000.0,
    ) -> None:
        self.rated_torque_nm = rated_torque_nm or settings.turbine.rated_generator_torque_nm  # ~43,093 Nm
        self.max_torque_nm = max_torque_nm or settings.turbine.max_generator_torque_nm        # ~47,402 Nm
        self.max_torque_rate_nm_s = max_torque_rate_nm_s

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Validate generator torque ceiling, rate limits, negative values, and spikes."""
        results: List[ValidationEvidence] = []
        if df.empty or "generator_torque_nm" not in df.columns:
            return results

        # 1. Invalid Negative Torque (Motoring Mode Violation)
        results.append(self._validate_negative_torque(df))

        # 2. Maximum Torque Clamping / Over-torque Limit
        results.append(self._validate_max_torque_limit(df))

        # 3. Dynamic Torque Spikes and Step Discontinuities
        results.append(self._validate_torque_spikes(df))

        # 4. Region 3 Torque Flatness / Power Constant Hold
        results.append(self._validate_region3_torque_holding(df))

        return results

    def _validate_negative_torque(self, df: pd.DataFrame) -> ValidationEvidence:
        generating = df[df["controller_state"].isin(["BELOW_RATED", "RATED_POWER", "ABOVE_RATED"])]
        if generating.empty:
            generating = df

        neg_torque = generating[generating["generator_torque_nm"] < -50.0]
        neg_count = len(neg_torque)
        min_torque = float(generating["generator_torque_nm"].min())

        status = ValidationStatus.PASS if neg_count == 0 else ValidationStatus.FAIL
        msg = (
            f"Zero invalid negative torque detected. Minimum observed torque: {min_torque:.1f} Nm."
            if neg_count == 0
            else f"INVALID MOTORING TORQUE: Generator acted as motor ({neg_count} samples < 0 Nm, min: {min_torque:.1f} Nm)!"
        )

        return ValidationEvidence(
            validator="torque_control.negative_torque",
            status=status,
            metric="negative_torque_samples",
            actual=neg_count,
            threshold=0,
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"min_torque_nm": round(min_torque, 1)},
        )

    def _validate_max_torque_limit(self, df: pd.DataFrame) -> ValidationEvidence:
        torque = df["generator_torque_nm"].dropna()
        max_t = float(torque.max()) if not torque.empty else 0.0

        if max_t <= (self.rated_torque_nm * 1.02):
            status = ValidationStatus.PASS
            msg = f"Torque strictly held within operational rated ceiling ({max_t:.1f} Nm <= {self.rated_torque_nm:.1f} Nm)."
        elif max_t <= self.max_torque_nm:
            status = ValidationStatus.WARNING
            msg = f"Torque in converter transient overload margin ({max_t:.1f} Nm <= {self.max_torque_nm:.1f} Nm peak limit)."
        else:
            status = ValidationStatus.FAIL
            msg = f"CONVERTER OVERTORQUE FAULT: Torque exceeded peak mechanical limit ({max_t:.1f} Nm > {self.max_torque_nm:.1f} Nm)!"

        return ValidationEvidence(
            validator="torque_control.max_limit",
            status=status,
            metric="peak_generator_torque_nm",
            actual=round(max_t, 1),
            threshold=round(self.max_torque_nm, 1),
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"rated_torque_nm": self.rated_torque_nm, "peak_limit_nm": self.max_torque_nm},
        )

    def _validate_torque_spikes(self, df: pd.DataFrame) -> ValidationEvidence:
        time = df["timestamp"]
        torque = df["generator_torque_nm"]
        torque_rate = compute_rate_of_change(torque, time).abs()

        max_rate = float(torque_rate.max()) if not torque_rate.empty else 0.0
        spikes = int((torque_rate > self.max_torque_rate_nm_s).sum())

        if spikes == 0:
            status = ValidationStatus.PASS
            msg = f"Converter torque demand smooth. Peak dQ/dt = {max_rate:.1f} Nm/s <= {self.max_torque_rate_nm_s:.1f} Nm/s."
        elif spikes < 4:
            status = ValidationStatus.WARNING
            msg = f"Isolated converter torque spike: {max_rate:.1f} Nm/s ({spikes} instances)."
        else:
            status = ValidationStatus.FAIL
            msg = f"Severe torque step discontinuity/chatter: {spikes} samples exceed {self.max_torque_rate_nm_s:.1f} Nm/s (max {max_rate:.1f} Nm/s)."

        return ValidationEvidence(
            validator="torque_control.torque_spikes",
            status=status,
            metric="max_torque_rate_nm_s",
            actual=round(max_rate, 1),
            threshold=round(self.max_torque_rate_nm_s, 1),
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"spike_count": spikes},
        )

    def _validate_region3_torque_holding(self, df: pd.DataFrame) -> ValidationEvidence:
        # Above rated wind (> 12 m/s), torque should remain near rated (43.09 kNm)
        region3 = df[df["wind_speed_mps"] > 13.0]
        if region3.empty:
            return ValidationEvidence(
                validator="torque_control.region3_holding",
                status=ValidationStatus.PASS,
                metric="region3_torque_mean_nm",
                actual=self.rated_torque_nm,
                threshold=f"{self.rated_torque_nm:.0f} +/- 5%",
                message="Wind remained sub-rated; Region 3 torque hold check skipped.",
            )

        mean_t = float(region3["generator_torque_nm"].mean())
        deviation_pct = abs(mean_t - self.rated_torque_nm) / self.rated_torque_nm * 100.0

        status = ValidationStatus.PASS if deviation_pct <= 5.0 else (ValidationStatus.WARNING if deviation_pct <= 10.0 else ValidationStatus.FAIL)
        msg = (
            f"Region 3 torque maintained at rated setpoint (mean: {mean_t:.1f} Nm, deviation: {deviation_pct:.2f}%)."
            if status == ValidationStatus.PASS
            else f"Region 3 torque deviation from rated setpoint: {deviation_pct:.2f}% (observed mean: {mean_t:.1f} Nm)."
        )

        return ValidationEvidence(
            validator="torque_control.region3_holding",
            status=status,
            metric="region3_torque_deviation_pct",
            actual=round(deviation_pct, 2),
            threshold=5.0,
            message=msg,
            severity="MEDIUM" if status != ValidationStatus.PASS else "LOW",
        )

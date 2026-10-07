"""Signal integrity, sensor dropout, sampling continuity, and physical range validation."""

from typing import List, Optional
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus


class SignalIntegrityValidator:
    """Validates raw telemetry signal quality, timestamp monotonicity, and sensor validity."""

    def __init__(self, dt_nominal: float = 0.05, max_gap_multiplier: float = 3.0) -> None:
        self.dt_nominal = dt_nominal
        self.max_gap_threshold = dt_nominal * max_gap_multiplier

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Execute comprehensive signal integrity suite on telemetry DataFrame."""
        results: List[ValidationEvidence] = []

        if df.empty:
            results.append(
                ValidationEvidence(
                    validator="signal_integrity.empty_check",
                    status=ValidationStatus.FAIL,
                    metric="dataset_row_count",
                    actual=0,
                    threshold=">= 1",
                    message="Telemetry dataset is completely empty.",
                    severity="CRITICAL",
                )
            )
            return results

        # 1. NaN and Missing Value Check
        results.append(self._check_nan_values(df))

        # 2. Timestamp Duplicate Check
        results.append(self._check_duplicate_timestamps(df))

        # 3. Timestamp Monotonicity and Sampling Gaps
        results.append(self._check_sampling_continuity(df))

        # 4. Out-of-Bounds Physical Sensor Checks
        results.extend(self._check_physical_sensor_limits(df))

        # 5. Sensor Freeze Detection
        results.append(self._check_sensor_freeze(df))

        return results

    def _check_nan_values(self, df: pd.DataFrame) -> ValidationEvidence:
        total_cells = df.size
        nan_cells = int(df.isna().sum().sum())
        nan_pct = float((nan_cells / total_cells) * 100.0) if total_cells > 0 else 0.0

        if nan_cells == 0:
            status = ValidationStatus.PASS
            msg = "Zero missing or NaN values detected across all telemetry channels."
        elif nan_pct < 1.0:
            status = ValidationStatus.WARNING
            msg = f"Low-frequency NaN dropout detected: {nan_cells} cells ({nan_pct:.2f}%)."
        else:
            status = ValidationStatus.FAIL
            msg = f"Critical sensor telemetry dropout: {nan_cells} cells ({nan_pct:.2f}%) are NaN."

        return ValidationEvidence(
            validator="signal_integrity.nan_dropout",
            status=status,
            metric="nan_ratio_pct",
            actual=round(nan_pct, 3),
            threshold=0.0,
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"nan_cells": nan_cells, "total_cells": total_cells},
        )

    def _check_duplicate_timestamps(self, df: pd.DataFrame) -> ValidationEvidence:
        duplicates = int(df["timestamp"].duplicated().sum())
        status = ValidationStatus.PASS if duplicates == 0 else ValidationStatus.FAIL
        msg = (
            "Timestamps are strictly unique."
            if duplicates == 0
            else f"Detected {duplicates} duplicated timestamp entries in telemetry stream."
        )

        return ValidationEvidence(
            validator="signal_integrity.timestamp_duplicates",
            status=status,
            metric="duplicate_timestamps",
            actual=duplicates,
            threshold=0,
            message=msg,
            severity="HIGH" if duplicates > 0 else "LOW",
        )

    def _check_sampling_continuity(self, df: pd.DataFrame) -> ValidationEvidence:
        time = df["timestamp"].dropna()
        diffs = time.diff().dropna()

        # Non-monotonic check (negative delta)
        negative_diffs = int((diffs <= 0).sum())
        if negative_diffs > 0:
            return ValidationEvidence(
                validator="signal_integrity.time_continuity",
                status=ValidationStatus.FAIL,
                metric="non_monotonic_timestamps",
                actual=negative_diffs,
                threshold=0,
                message=f"Telemetry time is non-monotonic ({negative_diffs} retroactive jumps).",
                severity="CRITICAL",
            )

        # Sampling gaps
        dt_max = float(diffs.max()) if not diffs.empty else 0.0
        gaps = diffs[diffs > self.max_gap_threshold]
        gap_count = len(gaps)

        if gap_count == 0:
            status = ValidationStatus.PASS
            msg = f"Continuous sampling verified. Maximum dt = {dt_max:.4f}s."
        elif gap_count < 3:
            status = ValidationStatus.WARNING
            msg = f"Minor sampling discontinuity: {gap_count} gaps > {self.max_gap_threshold:.3f}s (max dt = {dt_max:.3f}s)."
        else:
            status = ValidationStatus.FAIL
            msg = f"Unacceptable telemetry stream interruption: {gap_count} gaps exceed threshold (max dt = {dt_max:.3f}s)."

        return ValidationEvidence(
            validator="signal_integrity.sampling_continuity",
            status=status,
            metric="max_sampling_interval_sec",
            actual=round(dt_max, 4),
            threshold=round(self.max_gap_threshold, 4),
            message=msg,
            severity="MEDIUM" if status == ValidationStatus.WARNING else ("HIGH" if status == ValidationStatus.FAIL else "LOW"),
            details={"gap_count": gap_count},
        )

    def _check_physical_sensor_limits(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        evidences = []

        # Wind speed physically valid [0.0, 50.0 m/s]
        ws = df["wind_speed_mps"].dropna()
        if not ws.empty:
            neg_ws = int((ws < 0.0).sum())
            over_ws = int((ws > 50.0).sum())
            if neg_ws > 0 or over_ws > 0:
                evidences.append(
                    ValidationEvidence(
                        validator="signal_integrity.wind_speed_range",
                        status=ValidationStatus.FAIL,
                        metric="out_of_bounds_wind_speed",
                        actual=neg_ws + over_ws,
                        threshold=0,
                        message=f"Physically impossible wind speed sensor readings ({neg_ws} negative, {over_ws} > 50 m/s).",
                        severity="HIGH",
                    )
                )
            else:
                evidences.append(
                    ValidationEvidence(
                        validator="signal_integrity.wind_speed_range",
                        status=ValidationStatus.PASS,
                        metric="out_of_bounds_wind_speed",
                        actual=0,
                        threshold=0,
                        message="Wind speed measurements within physical atmospheric boundary [0, 50] m/s.",
                    )
                )

        # Pitch angle physically valid [-2.0, 95.0 deg]
        pitch = df["blade_pitch_deg"].dropna()
        if not pitch.empty:
            invalid_pitch = int(((pitch < -2.0) | (pitch > 95.0)).sum())
            status = ValidationStatus.PASS if invalid_pitch == 0 else ValidationStatus.FAIL
            evidences.append(
                ValidationEvidence(
                    validator="signal_integrity.blade_pitch_range",
                    status=status,
                    metric="invalid_pitch_samples",
                    actual=invalid_pitch,
                    threshold=0,
                    message=(
                        "Blade pitch angles conform to mechanical actuator envelope [-2.0, 95.0] deg."
                        if invalid_pitch == 0
                        else f"Blade pitch actuator range violation: {invalid_pitch} samples outside [-2, 95] deg."
                    ),
                    severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
                )
            )

        return evidences

    def _check_sensor_freeze(self, df: pd.DataFrame, freeze_window_samples: int = 50) -> ValidationEvidence:
        """Detect stuck sensor output where dynamic signal has zero variance for prolonged period."""
        ws = df["wind_speed_mps"].dropna()
        frozen_windows = 0
        if len(ws) >= freeze_window_samples:
            rolling_std = ws.rolling(window=freeze_window_samples).std().dropna()
            frozen_windows = int((rolling_std == 0.0).sum())

        status = ValidationStatus.PASS if frozen_windows == 0 else ValidationStatus.FAIL
        msg = (
            "Dynamic sensor variance confirmed (no frozen wind speed sensor detected)."
            if frozen_windows == 0
            else f"Wind speed sensor freeze detected across {frozen_windows} rolling evaluation windows."
        )

        return ValidationEvidence(
            validator="signal_integrity.sensor_freeze",
            status=status,
            metric="frozen_sample_windows",
            actual=frozen_windows,
            threshold=0,
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
        )

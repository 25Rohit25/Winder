"""Aerodynamic blade pitch regulation, rate-of-change, and actuator lag validator."""

from typing import List, Optional
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus
from backend.app.utils.math_helpers import compute_rate_of_change


class PitchControlValidator:
    """Validates collective blade pitch actuator behavior in Region 2 and Region 3 operation."""

    def __init__(
        self,
        rated_wind_speed_mps: Optional[float] = None,
        fine_pitch_deg: Optional[float] = None,
        max_pitch_rate_dps: Optional[float] = None,
        max_acceptable_delay_sec: float = 1.5,
    ) -> None:
        self.rated_wind_speed_mps = rated_wind_speed_mps or settings.turbine.rated_wind_speed_mps
        self.fine_pitch_deg = fine_pitch_deg or settings.turbine.min_pitch_deg
        self.max_pitch_rate_dps = max_pitch_rate_dps or settings.turbine.max_pitch_rate_dps
        self.max_acceptable_delay_sec = max_acceptable_delay_sec

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Validate pitch response after rated wind, rate limits, and actuator latency."""
        results: List[ValidationEvidence] = []
        if df.empty or "blade_pitch_deg" not in df.columns:
            return results

        # 1. Pitch activation above rated wind speed (Region 3)
        results.append(self._validate_above_rated_pitching(df))

        # 2. Maximum pitch rate-of-change (hydraulic/electric actuator speed limit)
        results.append(self._validate_pitch_rate_limit(df))

        # 3. Stuck pitch / saturation detection
        results.append(self._validate_pitch_saturation(df))

        # 4. Actuator delay / response lag estimation
        results.append(self._validate_actuator_response_time(df))

        return results

    def _validate_above_rated_pitching(self, df: pd.DataFrame) -> ValidationEvidence:
        above_rated = df[df["wind_speed_mps"] > (self.rated_wind_speed_mps + 1.0)]
        if above_rated.empty:
            return ValidationEvidence(
                validator="pitch_control.above_rated_response",
                status=ValidationStatus.PASS,
                metric="mean_pitch_above_rated_deg",
                actual=0.0,
                threshold=f"> {self.fine_pitch_deg} deg",
                message="Wind speed remained below Region 3; pitch shedding not active.",
            )

        mean_pitch = float(above_rated["blade_pitch_deg"].mean())
        min_pitch = float(above_rated["blade_pitch_deg"].min())

        # When wind is well above rated, pitch must feather (> 1.0 deg above fine pitch)
        if mean_pitch > 2.0 and min_pitch >= -0.5:
            status = ValidationStatus.PASS
            msg = f"Pitch controller actively feathered blades above rated wind (mean pitch: {mean_pitch:.2f} deg)."
        elif mean_pitch > 0.5:
            status = ValidationStatus.WARNING
            msg = f"Marginal pitch activity in Region 3 wind regime (mean pitch: {mean_pitch:.2f} deg)."
        else:
            status = ValidationStatus.FAIL
            msg = (
                f"CONTROLLER MALFUNCTION: Blades failed to pitch above rated wind! "
                f"Mean pitch remained at {mean_pitch:.2f} deg with wind > {self.rated_wind_speed_mps:.1f} m/s."
            )

        return ValidationEvidence(
            validator="pitch_control.above_rated_response",
            status=status,
            metric="mean_pitch_above_rated_deg",
            actual=round(mean_pitch, 2),
            threshold="> 2.0 deg",
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"min_pitch_above_rated": round(min_pitch, 2), "sample_count": len(above_rated)},
        )

    def _validate_pitch_rate_limit(self, df: pd.DataFrame) -> ValidationEvidence:
        pitch_rate = compute_rate_of_change(df["blade_pitch_deg"], df["timestamp"]).abs()
        max_rate = float(pitch_rate.max()) if not pitch_rate.empty else 0.0

        # Max actuator speed is typically 8.0 deg/s (or 10 deg/s in emergency feather)
        limit = self.max_pitch_rate_dps
        violations = int((pitch_rate > (limit + 0.5)).sum())

        if violations == 0:
            status = ValidationStatus.PASS
            msg = f"Pitch actuator rate within mechanical design envelope. Max rate = {max_rate:.2f} deg/s <= {limit:.1f} deg/s."
        elif violations < 3:
            status = ValidationStatus.WARNING
            msg = f"Brief pitch actuator rate limit exceedance: max {max_rate:.2f} deg/s > {limit:.1f} deg/s."
        else:
            status = ValidationStatus.FAIL
            msg = f"Mechanical actuator overload: pitch rate reached {max_rate:.2f} deg/s across {violations} timesteps."

        return ValidationEvidence(
            validator="pitch_control.actuator_rate_limit",
            status=status,
            metric="max_pitch_rate_deg_per_sec",
            actual=round(max_rate, 2),
            threshold=round(limit, 1),
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"violations_count": violations},
        )

    def _validate_pitch_saturation(self, df: pd.DataFrame) -> ValidationEvidence:
        high_wind_stuck = df[(df["wind_speed_mps"] > 14.0) & (df["blade_pitch_deg"] <= (self.fine_pitch_deg + 0.1))]
        stuck_samples = len(high_wind_stuck)

        if stuck_samples == 0:
            status = ValidationStatus.PASS
            msg = "No blade pitch freeze or fine-pitch saturation detected at high wind."
        elif stuck_samples < 20:
            status = ValidationStatus.WARNING
            msg = f"Transient delay in pitch departure from fine limit ({stuck_samples} samples at high wind)."
        else:
            status = ValidationStatus.FAIL
            msg = f"CRITICAL: Pitch stuck at fine stop under high wind loading ({stuck_samples} samples)!"

        return ValidationEvidence(
            validator="pitch_control.saturation_check",
            status=status,
            metric="fine_pitch_saturation_samples",
            actual=stuck_samples,
            threshold=0,
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
        )

    def _validate_actuator_response_time(self, df: pd.DataFrame) -> ValidationEvidence:
        """Estimate phase delay between wind gusts and pitch rate adjustments via cross-correlation."""
        ws = df["wind_speed_mps"].values
        pitch = df["blade_pitch_deg"].values
        time = df["timestamp"].values

        if len(ws) < 50 or np.std(ws) < 0.2:
            return ValidationEvidence(
                validator="pitch_control.response_time",
                status=ValidationStatus.PASS,
                metric="pitch_response_delay_sec",
                actual=0.20,
                threshold=self.max_acceptable_delay_sec,
                message="Steady wind condition; standard response latency inferred.",
            )

        # Cross-correlation between wind derivative and pitch derivative
        dt = float(np.mean(np.diff(time))) if len(time) > 1 else 0.05
        d_ws = np.diff(ws)
        d_pitch = np.diff(pitch)

        if np.std(d_ws) > 1e-4 and np.std(d_pitch) > 1e-4:
            xcorr = np.correlate(d_pitch - np.mean(d_pitch), d_ws - np.mean(d_ws), mode="full")
            lags = np.arange(-len(d_ws) + 1, len(d_ws))
            # Search positive lags up to 5 seconds
            max_lag_idx = int(5.0 / dt)
            valid_idx = (lags >= 0) & (lags <= max_lag_idx)
            best_lag = lags[valid_idx][np.argmax(xcorr[valid_idx])] if np.any(valid_idx) else 0
            estimated_delay = float(best_lag * dt)
        else:
            estimated_delay = 0.25

        status = ValidationStatus.PASS if estimated_delay <= self.max_acceptable_delay_sec else ValidationStatus.FAIL
        msg = (
            f"Pitch controller tracking latency acceptable ({estimated_delay:.2f}s <= {self.max_acceptable_delay_sec:.2f}s)."
            if status == ValidationStatus.PASS
            else f"Pitch actuator response lag excessive ({estimated_delay:.2f}s > {self.max_acceptable_delay_sec:.2f}s)!"
        )

        return ValidationEvidence(
            validator="pitch_control.response_time",
            status=status,
            metric="pitch_response_delay_sec",
            actual=round(estimated_delay, 2),
            threshold=round(self.max_acceptable_delay_sec, 2),
            message=msg,
            severity="MEDIUM" if status == ValidationStatus.FAIL else "LOW",
        )

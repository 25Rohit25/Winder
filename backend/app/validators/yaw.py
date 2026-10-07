"""Nacelle yaw alignment tracking, persistent offset, and controller state validator."""

from typing import List, Optional
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus


class YawValidator:
    """Validates nacelle yaw tracking error and wind vane alignment."""

    def __init__(
        self,
        max_yaw_error_deg: Optional[float] = None,
        max_persistent_error_deg: float = 6.0,
        rolling_window_sec: float = 30.0,
    ) -> None:
        self.max_yaw_error_deg = max_yaw_error_deg or settings.turbine.max_yaw_error_deg  # 10.0 deg
        self.max_persistent_error_deg = max_persistent_error_deg
        self.rolling_window_sec = rolling_window_sec

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Validate peak yaw misalignment and persistent directional offset."""
        results: List[ValidationEvidence] = []
        if df.empty or "nacelle_yaw_error" not in df.columns:
            return results

        yaw = df["nacelle_yaw_error"].dropna()
        if yaw.empty:
            return results

        # 1. Peak Instantaneous Yaw Error
        max_abs_yaw = float(yaw.abs().max())
        if max_abs_yaw <= self.max_yaw_error_deg:
            status = ValidationStatus.PASS
            msg = f"Nacelle yaw tracking tightly bounded (max error: {max_abs_yaw:.1f} deg <= {self.max_yaw_error_deg:.1f} deg)."
        elif max_abs_yaw <= (self.max_yaw_error_deg * 1.5):
            status = ValidationStatus.WARNING
            msg = f"Elevated transient yaw misalignment: peak {max_abs_yaw:.1f} deg > {self.max_yaw_error_deg:.1f} deg."
        else:
            status = ValidationStatus.FAIL
            msg = f"EXCESSIVE YAW TRACKING ERROR: Severe wind misdirection ({max_abs_yaw:.1f} deg > {self.max_yaw_error_deg * 1.5:.1f} deg)!"

        results.append(
            ValidationEvidence(
                validator="yaw.peak_error",
                status=status,
                metric="max_nacelle_yaw_error_deg",
                actual=round(max_abs_yaw, 2),
                threshold=round(self.max_yaw_error_deg, 1),
                message=msg,
                severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            )
        )

        # 2. Persistent Misalignment (Long-term Energy Loss & Fatigue)
        dt = float(df["timestamp"].diff().mean()) if "timestamp" in df.columns and len(df) > 1 else 0.05
        full_window = max(5, int(self.rolling_window_sec / dt))
        min_p = max(1, min(len(yaw) // 2, full_window // 2))
        rolling_mean = yaw.rolling(window=min(full_window, len(yaw)), min_periods=min_p).mean().abs().dropna()
        max_persistent = float(rolling_mean.max()) if not rolling_mean.empty else float(yaw.abs().mean())

        if max_persistent <= self.max_persistent_error_deg:
            p_status = ValidationStatus.PASS
            p_msg = f"Yaw tracking centered. Mean rolling error = {max_persistent:.2f} deg <= {self.max_persistent_error_deg:.1f} deg."
        elif max_persistent <= (self.max_persistent_error_deg * 1.5):
            p_status = ValidationStatus.WARNING
            p_msg = f"Persistent yaw bias detected: rolling average offset {max_persistent:.2f} deg exceeds {self.max_persistent_error_deg:.1f} deg."
        else:
            p_status = ValidationStatus.FAIL
            p_msg = f"YAW DRIVE FAILURE / SENSOR BIAS: Sustained aerodynamic misalignment of {max_persistent:.2f} deg!"

        results.append(
            ValidationEvidence(
                validator="yaw.persistent_misalignment",
                status=p_status,
                metric="max_rolling_yaw_error_deg",
                actual=round(max_persistent, 2),
                threshold=round(self.max_persistent_error_deg, 1),
                message=p_msg,
                severity="MEDIUM" if p_status == ValidationStatus.WARNING else ("HIGH" if p_status == ValidationStatus.FAIL else "LOW"),
            )
        )

        return results


class ControllerStateValidator:
    """Validates state machine transitions, illegal jumps, and unexpected shutdowns."""

    # Allowed forward/backward transitions
    LEGAL_TRANSITIONS = {
        "IDLE": ["IDLE", "STARTUP", "FAULT_TRIP"],
        "STARTUP": ["STARTUP", "BELOW_RATED", "SHUTDOWN", "FAULT_TRIP"],
        "BELOW_RATED": ["BELOW_RATED", "RATED_POWER", "ABOVE_RATED", "SHUTDOWN", "FAULT_TRIP"],
        "RATED_POWER": ["RATED_POWER", "BELOW_RATED", "ABOVE_RATED", "SHUTDOWN", "FAULT_TRIP"],
        "ABOVE_RATED": ["ABOVE_RATED", "RATED_POWER", "BELOW_RATED", "SHUTDOWN", "FAULT_TRIP"],
        "SHUTDOWN": ["SHUTDOWN", "IDLE", "FAULT_TRIP"],
        "FAULT_TRIP": ["FAULT_TRIP", "IDLE", "SHUTDOWN"],
        "EMERGENCY_STOP": ["EMERGENCY_STOP", "IDLE", "FAULT_TRIP"],
    }

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        results: List[ValidationEvidence] = []
        if df.empty or "controller_state" not in df.columns:
            return results

        states = df["controller_state"].values
        illegal_transitions = 0
        illegal_samples = []

        for i in range(len(states) - 1):
            curr_s = states[i]
            next_s = states[i + 1]
            if curr_s != next_s:
                allowed = self.LEGAL_TRANSITIONS.get(curr_s, [])
                if next_s not in allowed:
                    illegal_transitions += 1
                    illegal_samples.append((i, curr_s, next_s))

        status = ValidationStatus.PASS if illegal_transitions == 0 else ValidationStatus.FAIL
        msg = (
            "All supervisory controller state machine transitions strictly conform to control design."
            if illegal_transitions == 0
            else f"ILLEGAL STATE TRANSITION: Detected {illegal_transitions} invalid controller state jumps!"
        )

        results.append(
            ValidationEvidence(
                validator="controller_state.transitions",
                status=status,
                metric="illegal_state_transitions",
                actual=illegal_transitions,
                threshold=0,
                message=msg,
                severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
                details={"violations": illegal_samples[:5]},
            )
        )

        return results

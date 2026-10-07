"""Turbine rotor and generator overspeed safety threshold validator."""

from typing import List, Optional
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus


class OverspeedValidator:
    """Validates structural overspeed protection boundaries and emergency trip behavior.

    Boundary Specification:
    - Normal ceiling: 14.50 RPM.
    - Safety margin zone: (14.50, 15.00] RPM -> WARNING (controller pitch margin exhausted).
    - Emergency trip boundary: 15.00 RPM.
      - 14.99 RPM -> PASS / WARNING boundary check.
      - 15.00 RPM -> PASS / WARNING (at boundary).
      - 15.01 RPM -> FAIL (hard emergency trip violation).
    """

    def __init__(
        self,
        operational_ceiling_rpm: Optional[float] = None,
        overspeed_trip_rpm: Optional[float] = None,
    ) -> None:
        self.operational_ceiling_rpm = operational_ceiling_rpm or settings.turbine.max_rotor_speed_rpm  # 14.50
        self.overspeed_trip_rpm = overspeed_trip_rpm or settings.turbine.overspeed_trip_rpm              # 15.00

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Evaluate rotor speed against strict deterministic overspeed boundaries."""
        results: List[ValidationEvidence] = []
        if df.empty or "rotor_speed_rpm" not in df.columns:
            return results

        speed = df["rotor_speed_rpm"].dropna()
        if speed.empty:
            return results

        max_speed = float(speed.max())

        # Exact boundary evaluation
        if max_speed <= self.operational_ceiling_rpm:
            status = ValidationStatus.PASS
            msg = (
                f"Rotor speed securely below operational ceiling ({max_speed:.3f} RPM <= "
                f"{self.operational_ceiling_rpm:.2f} RPM)."
            )
            time_window = None
        elif max_speed <= self.overspeed_trip_rpm:
            # Between 14.50 and 15.00 inclusive
            status = ValidationStatus.WARNING
            msg = (
                f"Rotor speed in transient advisory margin ({max_speed:.3f} RPM > "
                f"{self.operational_ceiling_rpm:.2f} RPM, but <= trip limit {self.overspeed_trip_rpm:.2f} RPM)."
            )
            exceed_df = df[df["rotor_speed_rpm"] > self.operational_ceiling_rpm]
            time_window = [float(exceed_df["timestamp"].iloc[0]), float(exceed_df["timestamp"].iloc[-1])]
        else:
            # Strictly > 15.00 RPM (e.g. 15.01 RPM)
            status = ValidationStatus.FAIL
            msg = (
                f"CRITICAL SAFETY VIOLATION: Rotor overspeed trip limit breached! "
                f"Peak {max_speed:.3f} RPM strictly exceeds safety limit {self.overspeed_trip_rpm:.2f} RPM."
            )
            exceed_df = df[df["rotor_speed_rpm"] > self.overspeed_trip_rpm]
            time_window = [float(exceed_df["timestamp"].iloc[0]), float(exceed_df["timestamp"].iloc[-1])]

        duration_above_limit = 0.0
        if status != ValidationStatus.PASS and "timestamp" in df.columns:
            dt = df["timestamp"].diff().mean() or 0.05
            duration_above_limit = float((df["rotor_speed_rpm"] > self.operational_ceiling_rpm).sum() * dt)

        results.append(
            ValidationEvidence(
                validator="overspeed.trip_boundary",
                status=status,
                metric="peak_rotor_speed_rpm",
                actual=round(max_speed, 3),
                threshold=round(self.overspeed_trip_rpm, 2),
                message=msg,
                timestamp_range=time_window,
                severity="CRITICAL" if status == ValidationStatus.FAIL else ("MEDIUM" if status == ValidationStatus.WARNING else "LOW"),
                details={
                    "operational_ceiling_rpm": self.operational_ceiling_rpm,
                    "overspeed_trip_rpm": self.overspeed_trip_rpm,
                    "duration_above_ceiling_sec": round(duration_above_limit, 2),
                },
            )
        )

        # Emergency trip controller response verification
        if status == ValidationStatus.FAIL and "controller_state" in df.columns:
            has_tripped = bool((df["controller_state"].isin(["FAULT_TRIP", "EMERGENCY_STOP"])).any())
            trip_status = ValidationStatus.PASS if has_tripped else ValidationStatus.FAIL
            trip_msg = (
                "Supervisory controller appropriately transitioned to FAULT_TRIP upon overspeed detection."
                if has_tripped
                else "CONTROLLER MALFUNCTION: Controller failed to trigger emergency shutdown state during overspeed event!"
            )
            results.append(
                ValidationEvidence(
                    validator="overspeed.controller_action",
                    status=trip_status,
                    metric="overspeed_trip_state_commanded",
                    actual="TRIPPED" if has_tripped else "NO_TRIP",
                    threshold="TRIPPED",
                    message=trip_msg,
                    severity="CRITICAL" if trip_status == ValidationStatus.FAIL else "LOW",
                )
            )

        return results

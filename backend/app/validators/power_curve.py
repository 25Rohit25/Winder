"""IEC 61400-12 wind turbine power curve benchmark and tolerance band validator."""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.models.validation import ValidationEvidence, ValidationStatus


def reference_nrel_5mw_power_curve(wind_speed: float) -> float:
    """Ideal empirical power curve for NREL 5MW baseline reference turbine (kW)."""
    if wind_speed < 3.0 or wind_speed > 25.0:
        return 0.0
    elif wind_speed >= 11.4:
        return 5000.0
    else:
        # Region 2 cubic aerodynamic power progression between 3 m/s and 11.4 m/s
        # P = 5000 * ((v - 3.0) / (11.4 - 3.0))^2.7
        norm = (wind_speed - 3.0) / (11.4 - 3.0)
        return float(min(5000.0, 5000.0 * (norm ** 2.7)))


class PowerCurveValidator:
    """Validates electrical power production against certified IEC 61400-12 power envelope."""

    def __init__(
        self,
        rated_power_kw: Optional[float] = None,
        rated_wind_speed_mps: Optional[float] = None,
        cut_in_wind_speed_mps: Optional[float] = None,
        cut_out_wind_speed_mps: Optional[float] = None,
        tolerance_pct: float = 10.0,
    ) -> None:
        self.rated_power_kw = rated_power_kw or settings.turbine.rated_power_kw
        self.rated_wind_speed_mps = rated_wind_speed_mps or settings.turbine.rated_wind_speed_mps
        self.cut_in_wind_speed_mps = cut_in_wind_speed_mps or settings.turbine.cut_in_wind_speed_mps
        self.cut_out_wind_speed_mps = cut_out_wind_speed_mps or settings.turbine.cut_out_wind_speed_mps
        self.tolerance_pct = tolerance_pct

    def validate(self, df: pd.DataFrame) -> List[ValidationEvidence]:
        """Validate observed electrical power curve against theoretical aerodynamic benchmark."""
        results: List[ValidationEvidence] = []
        if df.empty or "electrical_power_kw" not in df.columns or "wind_speed_mps" not in df.columns:
            return results

        # 1. Rated Power Capping in Region 3
        results.append(self._validate_rated_power_cap(df))

        # 2. Maximum Power Curve Deviation across Wind Bins
        results.append(self._validate_binned_power_curve(df))

        # 3. Peak Power Overload Limit
        results.append(self._validate_peak_power_overload(df))

        return results

    def _validate_rated_power_cap(self, df: pd.DataFrame) -> ValidationEvidence:
        above_rated = df[df["wind_speed_mps"] >= (self.rated_wind_speed_mps + 1.0)]
        if above_rated.empty:
            return ValidationEvidence(
                validator="power_curve.rated_power_cap",
                status=ValidationStatus.PASS,
                metric="rated_power_tracking_pct",
                actual=100.0,
                threshold=f"{self.rated_power_kw:.0f} kW +/- 5%",
                message="Wind remained below rated speed; rated power capping check passed.",
            )

        mean_p = float(above_rated["electrical_power_kw"].mean())
        deviation_pct = abs(mean_p - self.rated_power_kw) / self.rated_power_kw * 100.0

        if deviation_pct <= 5.0:
            status = ValidationStatus.PASS
            msg = f"Rated power accurately governed at {mean_p:.1f} kW (deviation {deviation_pct:.2f}% <= 5.0%)."
        elif deviation_pct <= 12.0:
            status = ValidationStatus.WARNING
            msg = f"Mild power regulation drift above rated wind: observed {mean_p:.1f} kW (deviation {deviation_pct:.2f}%)."
        else:
            status = ValidationStatus.FAIL
            msg = (
                f"POWER CURVE DEFICIENCY: Turbine severely drifted from rated capacity! "
                f"Delivered {mean_p:.1f} kW vs {self.rated_power_kw:.0f} kW target (deviation {deviation_pct:.2f}% > 12.0%)."
            )

        return ValidationEvidence(
            validator="power_curve.rated_power_cap",
            status=status,
            metric="rated_power_deviation_pct",
            actual=round(deviation_pct, 2),
            threshold=5.0,
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details={"mean_power_kw": round(mean_p, 1), "rated_target_kw": self.rated_power_kw},
        )

    def _validate_binned_power_curve(self, df: pd.DataFrame) -> ValidationEvidence:
        # Bin data into 1.0 m/s wind bins between cut-in and cut-out
        df_op = df[df["controller_state"].isin(["BELOW_RATED", "RATED_POWER", "ABOVE_RATED"])]
        if df_op.empty:
            df_op = df

        bins = np.arange(self.cut_in_wind_speed_mps, min(22.0, df_op["wind_speed_mps"].max() + 1.0), 1.0)
        if len(bins) < 2:
            return ValidationEvidence(
                validator="power_curve.binned_deviation",
                status=ValidationStatus.PASS,
                metric="max_binned_power_deviation_pct",
                actual=0.0,
                threshold=self.tolerance_pct,
                message="Insufficient wind speed spread for IEC binned power curve evaluation.",
            )

        max_bin_dev = 0.0
        bin_records = {}

        for i in range(len(bins) - 1):
            v_low, v_high = bins[i], bins[i + 1]
            v_center = (v_low + v_high) / 2.0
            in_bin = df_op[(df_op["wind_speed_mps"] >= v_low) & (df_op["wind_speed_mps"] < v_high)]

            if len(in_bin) >= 10:
                p_meas = float(in_bin["electrical_power_kw"].mean())
                p_ref = reference_nrel_5mw_power_curve(v_center)
                if p_ref > 100.0:
                    dev_pct = abs(p_meas - p_ref) / self.rated_power_kw * 100.0
                    bin_records[f"{v_center:.1f}m/s"] = {"meas_kw": p_meas, "ref_kw": p_ref, "dev_pct": dev_pct}
                    if dev_pct > max_bin_dev:
                        max_bin_dev = dev_pct

        status = ValidationStatus.PASS if max_bin_dev <= self.tolerance_pct else (
            ValidationStatus.WARNING if max_bin_dev <= (self.tolerance_pct * 1.5) else ValidationStatus.FAIL
        )
        msg = (
            f"Measured power curve conforms to IEC 61400-12 reference band (max bin deviation: {max_bin_dev:.2f}%)."
            if status == ValidationStatus.PASS
            else f"Significant power curve discrepancy: maximum bin deviation {max_bin_dev:.2f}% exceeds {self.tolerance_pct:.1f}% tolerance."
        )

        return ValidationEvidence(
            validator="power_curve.binned_deviation",
            status=status,
            metric="max_binned_power_deviation_pct",
            actual=round(max_bin_dev, 2),
            threshold=round(self.tolerance_pct, 1),
            message=msg,
            severity="HIGH" if status == ValidationStatus.FAIL else "LOW",
            details=bin_records,
        )

    def _validate_peak_power_overload(self, df: pd.DataFrame) -> ValidationEvidence:
        power = df["electrical_power_kw"].dropna()
        max_p = float(power.max()) if not power.empty else 0.0
        overload_ceiling = self.rated_power_kw * 1.10  # 110% = 5500 kW

        status = ValidationStatus.PASS if max_p <= overload_ceiling else ValidationStatus.FAIL
        msg = (
            f"Peak active power remained within electrical generator overload threshold ({max_p:.1f} kW <= {overload_ceiling:.1f} kW)."
            if status == ValidationStatus.PASS
            else f"GENERATOR OVERLOAD TRIP: Power exceeded 110% rated maximum ({max_p:.1f} kW > {overload_ceiling:.1f} kW)!"
        )

        return ValidationEvidence(
            validator="power_curve.peak_overload",
            status=status,
            metric="peak_electrical_power_kw",
            actual=round(max_p, 1),
            threshold=round(overload_ceiling, 1),
            message=msg,
            severity="CRITICAL" if status == ValidationStatus.FAIL else "LOW",
        )

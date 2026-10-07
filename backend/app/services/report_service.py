"""Dual-engine report generation service producing LaTeX source and certified PDF documents."""

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
import jinja2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.app.core.config import settings
from backend.app.core.exceptions import ReportGenerationError
from backend.app.core.logging import setup_logger
from backend.app.models.report import ReportConfig, ReportMetadata
from backend.app.models.validation import ValidationRunSummary, ValidationStatus


class ReportService:
    """Manages compilation of LaTeX artifacts and PDF certification reports."""

    def __init__(self) -> None:
        self.logger = setup_logger("windctrl.reports")
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(settings.templates_dir)),
            variable_start_string="<<",
            variable_end_string=">>",
            block_start_string="<%",
            block_end_string="%>",
            autoescape=False,
        )

    def generate_report(
        self,
        summary: ValidationRunSummary,
        config: Optional[ReportConfig] = None,
        telemetry_df: Optional[pd.DataFrame] = None,
    ) -> ReportMetadata:
        """Generate both LaTeX source (.tex) and compiled audit PDF."""
        cfg = config or ReportConfig()
        report_id = f"cert-{summary.run_id}"
        out_dir = settings.reports_dir / summary.run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        tex_filename = f"validation_report_{summary.run_id}.tex"
        tex_path = out_dir / tex_filename
        pdf_path = out_dir / f"validation_report_{summary.run_id}.pdf"
        chart_path = out_dir / f"telemetry_chart_{summary.run_id}.png"

        # 1. Generate Telemetry Chart if DataFrame is provided
        if telemetry_df is not None and not telemetry_df.empty:
            self._generate_chart_figure(telemetry_df, chart_path)

        # 2. Render LaTeX Source
        try:
            template = self.jinja_env.get_template("validation_report.tex.j2")
            rendered_tex = template.render(summary=summary, config=cfg)
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(rendered_tex)
            self.logger.info(f"LaTeX document generated: {tex_path}")
        except Exception as exc:
            self.logger.error(f"Failed to render LaTeX template: {exc}")
            raise ReportGenerationError(f"LaTeX template error: {exc}") from exc

        # 3. Attempt pdflatex Compilation or execute ReportLab Fallback
        pdf_generated = False
        engine_used = "latex"

        if shutil.which(settings.latex_cmd):
            try:
                self.logger.info(f"Compiling PDF via {settings.latex_cmd}...")
                proc = subprocess.run(
                    [settings.latex_cmd, "-interaction=nonstopmode", tex_filename],
                    cwd=str(out_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                )
                if proc.returncode == 0 and pdf_path.exists():
                    pdf_generated = True
                    engine_used = "pdflatex"
            except Exception as e:
                self.logger.warning(f"pdflatex invocation failed ({e}); switching to ReportLab engine.")

        if not pdf_generated:
            # High-fidelity ReportLab compilation
            self.logger.info(f"Compiling certification report using ReportLab engine to {pdf_path}...")
            self._generate_reportlab_pdf(summary, cfg, pdf_path, chart_path if chart_path.exists() else None)
            pdf_generated = pdf_path.exists()
            engine_used = "reportlab_dual_engine"

        return ReportMetadata(
            report_id=report_id,
            run_id=summary.run_id,
            dataset_name=summary.dataset_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            tex_path=str(tex_path),
            pdf_path=str(pdf_path) if pdf_generated else None,
            pdf_generated=pdf_generated,
            engine_used=engine_used,
        )

    def _generate_chart_figure(self, df: pd.DataFrame, target_path: Path) -> None:
        """Render high-resolution multi-panel telemetry plot for report."""
        fig, axes = plt.subplots(3, 2, figsize=(11, 8.5), dpi=180)
        t = df["timestamp"]

        # Wind speed
        axes[0, 0].plot(t, df["wind_speed_mps"], color="#0284c7", lw=1.2)
        axes[0, 0].axhline(11.4, color="#dc2626", ls="--", lw=1.0, label="Rated (11.4 m/s)")
        axes[0, 0].set_ylabel("Wind Speed [m/s]")
        axes[0, 0].set_title("Hub-Height Wind Speed", fontsize=10, fontweight="bold")
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend(loc="upper right", fontsize=8)

        # Rotor speed
        axes[0, 1].plot(t, df["rotor_speed_rpm"], color="#16a34a", lw=1.2)
        axes[0, 1].axhline(15.0, color="#dc2626", ls="--", lw=1.0, label="Trip Limit (15.0 RPM)")
        axes[0, 1].set_ylabel("Rotor Speed [RPM]")
        axes[0, 1].set_title("Low-Speed Shaft Kinematics", fontsize=10, fontweight="bold")
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend(loc="upper right", fontsize=8)

        # Blade pitch
        axes[1, 0].plot(t, df["blade_pitch_deg"], color="#9333ea", lw=1.2)
        axes[1, 0].set_ylabel("Blade Pitch [deg]")
        axes[1, 0].set_title("Collective Blade Pitch Control Response", fontsize=10, fontweight="bold")
        axes[1, 0].grid(True, alpha=0.3)

        # Generator torque
        axes[1, 1].plot(t, df["generator_torque_nm"] / 1000.0, color="#ea580c", lw=1.2)
        axes[1, 1].axhline(43.09, color="#475569", ls="--", lw=1.0, label="Rated (43.1 kNm)")
        axes[1, 1].set_ylabel("Gen Torque [kNm]")
        axes[1, 1].set_title("Generator Torque Demand", fontsize=10, fontweight="bold")
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].legend(loc="upper right", fontsize=8)

        # Electrical power
        axes[2, 0].plot(t, df["electrical_power_kw"], color="#0d9488", lw=1.2)
        axes[2, 0].axhline(5000.0, color="#dc2626", ls="--", lw=1.0, label="Rated Capacity (5000 kW)")
        axes[2, 0].set_ylabel("Active Power [kW]")
        axes[2, 0].set_xlabel("Time [s]")
        axes[2, 0].set_title("Active Grid Power Output", fontsize=10, fontweight="bold")
        axes[2, 0].grid(True, alpha=0.3)
        axes[2, 0].legend(loc="upper right", fontsize=8)

        # Nacelle yaw error
        axes[2, 1].plot(t, df["nacelle_yaw_error"], color="#e11d48", lw=1.2)
        axes[2, 1].axhline(10.0, color="#f59e0b", ls="--", lw=1.0)
        axes[2, 1].axhline(-10.0, color="#f59e0b", ls="--", lw=1.0, label="10 deg Envelope")
        axes[2, 1].set_ylabel("Yaw Error [deg]")
        axes[2, 1].set_xlabel("Time [s]")
        axes[2, 1].set_title("Nacelle Wind Alignment Error", fontsize=10, fontweight="bold")
        axes[2, 1].grid(True, alpha=0.3)
        axes[2, 1].legend(loc="upper right", fontsize=8)

        plt.tight_layout()
        plt.savefig(target_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

    def _generate_reportlab_pdf(
        self,
        summary: ValidationRunSummary,
        config: ReportConfig,
        target_path: Path,
        chart_path: Optional[Path] = None,
    ) -> None:
        """Compile certification PDF with styling matching Siemens industrial documents."""
        doc = SimpleDocTemplate(
            str(target_path),
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.HexColor("#0f2240"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor("#007299"),
            spaceAfter=15,
        )
        h2_style = ParagraphStyle(
            "H2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=colors.HexColor("#0f2240"),
            spaceBefore=12,
            spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
        )
        verdict_color = (
            colors.HexColor("#15803d")
            if summary.overall_status == ValidationStatus.PASS
            else (colors.HexColor("#b45309") if summary.overall_status == ValidationStatus.WARNING else colors.HexColor("#b91c1c"))
        )

        elements = []

        # 1. Header Banner
        header_data = [
            [
                Paragraph("<b>WIND TURBINE CONTROLLER VALIDATION REPORT</b>", title_style),
            ],
            [
                Paragraph(f"<b>Technical Audit Certificate</b> &bull; Standard: {config.standard} &bull; Model: {config.turbine_model}", subtitle_style),
            ],
        ]
        t_header = Table(header_data, colWidths=[540])
        t_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 14))

        # 2. Executive Summary Block
        verdict_text = f"<font size='18' color='{verdict_color.hexval()}'><b>OVERALL VERDICT: {summary.overall_status.value}</b></font><br/><br/>" \
                       f"<b>Validation Score:</b> {summary.validation_score}/100 &nbsp;|&nbsp; " \
                       f"<b>Tests Evaluated:</b> {summary.total_tests} &nbsp;|&nbsp; " \
                       f"<b>Passed:</b> {summary.passed_count} &nbsp;|&nbsp; " \
                       f"<b>Warnings:</b> {summary.warning_count} &nbsp;|&nbsp; " \
                       f"<b>Failed:</b> {summary.failed_count}"

        meta_text = f"<b>Run ID:</b> {summary.run_id}<br/>" \
                    f"<b>Dataset:</b> {summary.dataset_name}<br/>" \
                    f"<b>Scenario:</b> {summary.scenario_type}<br/>" \
                    f"<b>Authority:</b> {config.organization}<br/>" \
                    f"<b>Engineer:</b> {config.author}<br/>" \
                    f"<b>Execution:</b> {summary.execution_duration_ms:.1f} ms"

        exec_table = Table(
            [[Paragraph(verdict_text, body_style), Paragraph(meta_text, body_style)]],
            colWidths=[310, 230],
        )
        exec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f1f5f9")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#ffffff")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(exec_table)
        elements.append(Spacer(1, 14))

        # 3. Physical KPIs Table
        elements.append(Paragraph("1. Engineering Physical Key Performance Indicators", h2_style))
        kpi_data = [
            ["Metric Channel", "Observed", "Threshold Limit", "Compliance"],
            ["Max Rotor Speed", f"{summary.max_rotor_speed_rpm} RPM", "15.00 RPM", "PASS" if summary.max_rotor_speed_rpm <= 15.0 else "FAIL"],
            ["Max Generator Torque", f"{summary.max_generator_torque_nm} Nm", "47,402.9 Nm", "PASS" if summary.max_generator_torque_nm <= 47402.9 else "FAIL"],
            ["Peak Active Power", f"{summary.max_electrical_power_kw} kW", "5,500.0 kW", "PASS" if summary.max_electrical_power_kw <= 5500.0 else "FAIL"],
            ["Power Curve Deviation", f"{summary.max_power_deviation_pct}%", "10.0%", "PASS" if summary.max_power_deviation_pct <= 10.0 else "FAIL"],
            ["Pitch Actuator Latency", f"{summary.pitch_response_time_sec} s", "1.50 s", "PASS" if summary.pitch_response_time_sec <= 1.50 else "FAIL"],
            ["Peak Yaw Misalignment", f"{summary.max_yaw_error_deg} deg", "10.0 deg", "PASS" if summary.max_yaw_error_deg <= 10.0 else "FAIL"],
            ["Signal Completeness", f"{summary.signal_completeness_pct}%", "99.0%", "PASS" if summary.signal_completeness_pct >= 99.0 else "FAIL"],
        ]
        t_kpi = Table(kpi_data, colWidths=[180, 120, 130, 110])
        t_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2240")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 14))

        # 4. Embedded Telemetry Plot
        if chart_path and chart_path.exists():
            elements.append(Paragraph("2. Telemetry Signal Review", h2_style))
            elements.append(Image(str(chart_path), width=540, height=270))
            elements.append(Spacer(1, 14))

        # 5. Test Evidence Matrix
        elements.append(Paragraph("3. Structured Verification Evidence Log", h2_style))
        ev_data = [["Rule ID", "Status", "Metric (Actual vs Limit)", "Engineering Diagnostic"]]
        for ev in summary.results[:12]:  # Show top 12 rules
            status_cell = f"<font color='{colors.HexColor('#15803d' if ev.status == ValidationStatus.PASS else '#b91c1c').hexval()}'><b>{ev.status.value}</b></font>"
            ev_data.append([
                Paragraph(f"<font size='7'>{ev.validator}</font>", body_style),
                Paragraph(status_cell, body_style),
                Paragraph(f"<font size='7'>{ev.metric}: <b>{ev.actual}</b> (Thr: {ev.threshold})</font>", body_style),
                Paragraph(f"<font size='7'>{ev.message}</font>", body_style),
            ])
        t_ev = Table(ev_data, colWidths=[120, 50, 160, 210])
        t_ev.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#007299")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(t_ev)
        elements.append(Spacer(1, 16))

        # 6. Sign-off Stamp Block
        sign_text = "<b>AUDIT SIGN-OFF:</b> Certified that this automated assessment was executed with strict deterministic rules.<br/>" \
                    f"Controls Engineering Lead: <i>{config.author}</i> &nbsp;|&nbsp; Date: {summary.timestamp[:10]}"
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f2240"), spaceAfter=6))
        elements.append(Paragraph(sign_text, body_style))

        doc.build(elements)

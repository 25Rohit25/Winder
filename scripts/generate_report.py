"""Automated command-line interface for LaTeX and PDF report compilation."""

import argparse
import os
import sys
from pathlib import Path

# Add repository root to pythonpath
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.core.config import settings
from backend.app.models.report import ReportConfig
from backend.app.services.controller_validator import ControllerValidationEngine
from backend.app.services.ingestion import load_telemetry_csv
from backend.app.services.report_service import ReportService


def main():
    parser = argparse.ArgumentParser(description="WindCtrl Validate Report Generator")
    parser.add_argument("dataset", nargs="?", default="data/baseline/normal_run.csv", help="Input telemetry CSV")
    parser.add_argument("--author", default="Lead Validation Engineer", help="Report author")
    parser.add_argument("--org", default="Wind Energy Systems Division", help="Issuing organization")
    args = parser.parse_args()

    input_path = Path(args.dataset)
    if not input_path.is_absolute():
        input_path = repo_root / input_path

    if not input_path.exists():
        print(f"Dataset path not found: {input_path}")
        sys.exit(1)

    print("=" * 76)
    print(" WindCtrl Validate - Automated Certification Report Compiler")
    print(f" Ingesting Telemetry: {input_path.name}")
    print("=" * 76)

    # 1. Run validation
    df = load_telemetry_csv(input_path)
    engine = ControllerValidationEngine()
    summary = engine.run_validation(df, dataset_name=input_path.name, scenario_type=input_path.stem)
    print(f"[+] Validation complete: {summary.overall_status.value} (Score: {summary.validation_score:.1f}/100)")

    # 2. Compile report
    config = ReportConfig(author=args.author, organization=args.org)
    report_service = ReportService()
    meta = report_service.generate_report(summary, config=config, telemetry_df=df)

    print(f"[+] LaTeX Source: {meta.tex_path} ({os.path.getsize(meta.tex_path)} bytes)")
    if meta.pdf_path and os.path.exists(meta.pdf_path):
        print(f"[+] Audit PDF:    {meta.pdf_path} ({os.path.getsize(meta.pdf_path)} bytes)")
        print(f"[+] Compiler Engine: {meta.engine_used}")
    else:
        print("[-] PDF could not be compiled directly. Use Docker or pdflatex.")

    print("\nReport generation completed successfully.")


if __name__ == "__main__":
    main()

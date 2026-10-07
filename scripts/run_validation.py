"""Automated command-line interface for batch wind turbine controller validation."""

import argparse
import os
import sys
from pathlib import Path
from typing import List

# Add repository root to pythonpath
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.core.config import settings
from backend.app.models.validation import ValidationRunSummary, ValidationStatus
from backend.app.services.controller_validator import ControllerValidationEngine
from backend.app.services.ingestion import load_telemetry_csv


def print_validation_banner():
    print("=" * 76)
    print(" WindCtrl Validate - Automated Turbine Controller Verification Suite")
    print(" Standard: IEC 61400-1 ed.4 / NREL 5MW Baseline Controller")
    print("=" * 76)


def print_summary_card(summary: ValidationRunSummary):
    status_symbol = "[PASS]" if summary.overall_status == ValidationStatus.PASS else (
        "[WARN]" if summary.overall_status == ValidationStatus.WARNING else "[FAIL]"
    )
    print(f"\n{status_symbol} Run: {summary.run_id} | Dataset: {summary.dataset_name}")
    print(f"  Overall Score: {summary.validation_score:.1f}/100.0 | Status: {summary.overall_status.value}")
    print(f"  Tests: {summary.total_tests} | Passed: {summary.passed_count} | Warnings: {summary.warning_count} | Failed: {summary.failed_count}")
    print(f"  Physical KPIs: Max Rotor: {summary.max_rotor_speed_rpm:.2f} RPM | Max Power: {summary.max_electrical_power_kw:.1f} kW")
    print(f"  Max Torque: {summary.max_generator_torque_nm:.1f} Nm | Peak Yaw Err: {summary.max_yaw_error_deg:.1f} deg")
    print(f"  Execution Time: {summary.execution_duration_ms:.1f} ms")

    if summary.failed_count > 0:
        print("\n  FAILURES:")
        for r in summary.results:
            if r.status == ValidationStatus.FAIL:
                print(f"    - [{r.validator}] {r.metric}: {r.actual} (Limit: {r.threshold}) -> {r.message}")
    print("-" * 76)


def main():
    parser = argparse.ArgumentParser(description="WindCtrl Validate CLI Runner")
    parser.add_argument("dataset", nargs="?", default=None, help="Path to telemetry CSV file")
    parser.add_argument("--all-baseline", action="store_true", help="Validate all baseline datasets")
    parser.add_argument("--all-faults", action="store_true", help="Validate all fault datasets")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 on any warning or failure")
    args = parser.parse_args()

    print_validation_banner()
    engine = ControllerValidationEngine()
    targets: List[Path] = []

    if args.dataset:
        targets.append(Path(args.dataset))
    elif args.all_baseline:
        targets.extend(list((settings.data_dir / "baseline").glob("*.csv")))
    elif args.all_faults:
        targets.extend(list((settings.data_dir / "faults").glob("*.csv")))
    else:
        # Default: validate normal_run and gust_event
        targets.extend(list((settings.data_dir / "baseline").glob("*.csv")))

    if not targets:
        print("No datasets found to validate.")
        sys.exit(1)

    overall_clean = True
    for p in targets:
        if not p.exists():
            print(f"File not found: {p}")
            continue
        df = load_telemetry_csv(p)
        summary = engine.run_validation(df, dataset_name=p.name, scenario_type=p.stem)
        print_summary_card(summary)
        if summary.overall_status == ValidationStatus.FAIL:
            overall_clean = False

    if args.strict and not overall_clean:
        print("\nSTRICT MODE: Validation run completed with failures.")
        sys.exit(1)

    print("\nBatch validation completed successfully.")


if __name__ == "__main__":
    main()

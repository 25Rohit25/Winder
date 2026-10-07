# Design Decisions Record (ADR)

This document formalizes the engineering rationale, constraints, evaluated alternatives, and trade-offs behind foundational architectural decisions in the **WindCtrl Validate** platform.

---

## 1. Why Python Handles System Orchestration and API Services

### Context
Industrial controller validation requires ingesting large high-frequency time-series datasets, running matrix operations, executing rule logic, exposing REST APIs, and coordinating CI/CD pipelines.

### Decision
Adopt **Python 3.12** as the core orchestration and service language, leveraging **FastAPI**, **Pydantic v2**, and **Pandas/NumPy**.

### Alternatives Considered
- **C++ / Rust**: High throughput and memory safety, but slower iteration for rapid rule tweaking and lacks the rich data ecosystem of Pandas/ReportLab/Hypothesis.
- **Pure MATLAB**: Excellent matrix math, but poor REST API support, heavy licensing hurdles in headless CI pipelines, and suboptimal web integration.

### Trade-offs
- *Pros*: Vast ecosystem for numerical analysis, rapid API development with OpenAPI auto-generation, native cross-platform deployment.
- *Cons*: Higher runtime memory footprint than compiled languages like Rust; mitigated by vectorized NumPy operations and chunked streaming.

---

## 2. Why Standalone MATLAB Functions are Maintained Alongside Python

### Context
Turbine controls engineering teams at original equipment manufacturers (OEMs like Siemens Gamesa, Vestas, GE Vernova) predominantly develop control loops in MATLAB/Simulink and FAST/OpenFAST.

### Decision
Provide fully compliant standalone MATLAB `.m` scripts (`analyze_controller.m`, `validate_power_curve.m`, `validate_rotor_speed.m`, `validate_pitch_response.m`) mirror-matched with Python equivalents.

### Alternatives Considered
- **MATLAB Compiler SDK / Engine API for Python**: Requires runtime license servers and proprietary runtime binaries on CI nodes.
- **Python-Only Platform**: Leaves out legacy engineering workflows used by aero-elastic simulation teams.

### Trade-offs
- *Pros*: Engineers can run validation directly within MATLAB interactive command line without Python setup, while CI runs the headless Python pipeline license-free.
- *Cons*: Dual maintenance of analytical logic across two syntax sets; mitigated by strict unit test regression comparisons.

---

## 3. Why Validation Rules are Deterministic Instead of LLM-Based

### Context
Modern AI tools are frequently proposed for pattern detection. However, turbine control validation is a safety-critical discipline subject to IEC 61400 standards and DNV-GL certification audits.

### Decision
Implement **100% deterministic mathematical, physical, and state-machine validators**.

### Alternatives Considered
- **LLM Prompting on Telemetry Summaries**: Highly non-deterministic, hallucinates failure modes, violates reproducible safety audit requirements.
- **Unsupervised Anomaly Detection (Isolation Forest, Autoencoders)**: Can detect statistical drift, but cannot provide exact compliance certification against a standard limit (e.g., exactly 15.00 RPM).

### Trade-offs
- *Pros*: Exact mathematical reproducibility, explicit audit trail, zero hallucinations, fast sub-second execution, strict boundary testability.
- *Cons*: Rules must be explicitly authored by domain experts; mitigated by modular validator interface.

---

## 4. Why Synthetic Telemetry Uses Deterministic Random Seeds

### Context
Developing and testing a validation system without commercial field SCADA data requires realistic synthetic aero-elastic datasets.

### Decision
All synthetic signal generation runs use **explicit, deterministic random number generator seeds** (`numpy.random.default_rng(seed)`).

### Alternatives Considered
- **Purely Random Runs**: Tests would fluctuate and produce flaky CI/CD test results.
- **Static Hardcoded CSV Recordings**: Difficult to parameterize with varying gust amplitudes and fault severities.

### Trade-offs
- *Pros*: 100% bit-level reproducibility of test runs, deterministic failure benchmarks, regression predictability.
- *Cons*: Scenarios require deliberate seed management when testing new edge cases.

---

## 5. Why Every Validation Check Emits Structured Evidence

### Context
A simple boolean `true/false` return value fails to provide actionable root-cause diagnostic information when a controller test fails.

### Decision
Every validator emits a structured `ValidationEvidence` schema:
```json
{
  "validator": "overspeed.trip_boundary",
  "status": "PASS | WARNING | FAIL",
  "metric": "peak_rotor_speed_rpm",
  "actual": 15.35,
  "threshold": 15.00,
  "message": "CRITICAL SAFETY VIOLATION: Rotor overspeed trip limit breached!",
  "timestamp_range": [26.4, 34.2],
  "severity": "CRITICAL",
  "details": { "duration_above_ceiling_sec": 7.8 }
}
```

### Alternatives Considered
- **Flat Log Strings**: Hard to parse by dashboards and reporting templates.
- **Simple Boolean Flags**: Lacks numerical traceability back to raw sensor data.

### Trade-offs
- *Pros*: Direct consumption by frontend dashboards, automated LaTeX report table rendering, and CI audit logs.
- *Cons*: Modest memory overhead for storing evidence lists; negligible for typical test lengths.

---

## 6. Why Reports are Generated Directly from Validation Result State

### Context
Engineering certification reports must represent the true, uncorrupted outcome of a specific validation execution.

### Decision
Both LaTeX source (`.tex`) and compiled audit PDFs are rendered directly from the `ValidationRunSummary` domain model without intermediate human editing.

### Alternatives Considered
- **Manual Word / LaTeX Documentation**: Error-prone, disconnected from code commits, prone to human error.
- **Post-hoc Report Scraping**: Reading logs to stitch together a report.

### Trade-offs
- *Pros*: Guaranteed traceability from raw signal -> validation engine -> formal PDF audit certificate.
- *Cons*: Layout is constrained to predefined engineering templates.

---

## 7. Why CI Runs Golden-Dataset Regression Suites

### Context
Changes to controller parameters, filter time constants, or validator thresholds can inadvertently desensitize fault detection or introduce false alarms on clean runs.

### Decision
Every CI build runs regression tests across all 7 benchmark datasets, verifying that clean datasets produce zero false positives and that all 10 injected fault classes are definitively flagged.

### Alternatives Considered
- **Unit Tests Only on Isolated Functions**: Fails to test full drivetrain coupling and multi-rule interaction.

### Trade-offs
- *Pros*: Guarantees that regression bugs in validation sensitivity are trapped before merging to `main`.
- *Cons*: Adds ~3 seconds to CI test execution time.

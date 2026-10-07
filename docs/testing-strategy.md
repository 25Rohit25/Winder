# Testing Strategy & Quality Assurance

The testing architecture follows the automated testing pyramid tailored for safety-critical industrial controls validation.

## 1. Test Categories

### Unit & Boundary Tests (`backend/tests/unit/`)
- Tests individual validator classes in complete isolation.
- Evaluates exact mathematical boundaries:
  - **Rotor Speed 15.00 RPM**: Tests 14.49 (PASS), 14.50 (PASS), 14.51 (WARNING), 14.99 (WARNING), 15.00 (WARNING), 15.01 (FAIL).
  - **Torque Peak 47,402.91 Nm**: Tests rated, margin, and hard trip boundaries.
  - **Pitch Slew Rate 8.00 deg/s**: Tests actuator acceleration step changes.

### Property-Based Invariance Tests (`backend/tests/property/`)
- Powered by **Hypothesis**.
- Validates properties across arbitrary numerical domains:
  - Validation score is bounded in $[0.0, 100.0]$ regardless of test counts.
  - Scoring function is strictly monotonic with respect to test failures.
  - Trigonometric and kinematic unit conversions are reversible without loss of precision.

### Integration Pipeline Tests (`backend/tests/integration/`)
- Verifies complete data flow: CSV loading $\to$ schema validation $\to$ 7 validators $\to$ KPI metrics $\to$ summary output.
- Tests FastAPI REST endpoints with `TestClient` across all methods.

### Regression Benchmark Suite (`backend/tests/regression/`)
- Golden dataset testing ensuring that clean baseline runs produce no false positives (`failed_count == 0`), and all known injected fault scenarios trigger appropriate failure verdicts.

## 2. Running Test Suites

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage report
pytest backend/tests/ --cov=backend/app --cov-report=term-missing

# Run exact boundary tests only
pytest backend/tests/unit/test_exact_threshold_boundaries.py -v

# Run property-based tests
pytest backend/tests/property/ -v
```

# REST API Reference

The WindCtrl Validate backend exposes an OpenAPI 3.1 compliant REST API for telemetry ingestion, validation execution, fault synthesis, and report compilation.

Base URL: `http://localhost:8000/api/v1`
Interactive Docs: `http://localhost:8000/docs`

---

## 1. System Health

### `GET /api/v1/health`
Returns runtime status, turbine parameters, and system diagnostics.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "app_name": "WindCtrl Validate",
  "version": "1.0.0",
  "environment": "development",
  "python_version": "3.12.6",
  "turbine_model": "NREL 5MW Baseline (IEC Class IB)",
  "diagnostics": {
    "baseline_datasets_ready": true,
    "fault_datasets_ready": true,
    "pdf_fallback_enabled": true
  }
}
```

---

## 2. Telemetry Datasets

### `GET /api/v1/datasets`
Lists all available baseline, fault, and generated CSV telemetry files.

### `POST /api/v1/datasets/upload`
Uploads a new telemetry CSV file (`multipart/form-data`).

### `GET /api/v1/datasets/{filename}/telemetry`
Retrieves time-series data vectors with optional stride downsampling.

---

## 3. Controller Validation

### `POST /api/v1/validation/run`
Executes validation checks on a designated dataset.

**Request Body**:
```json
{
  "dataset_name": "normal_run.csv",
  "scenario_type": "operational",
  "run_id": "optional-custom-id"
}
```

**Response `200 OK`**: Returns full `ValidationRunSummary` model.

### `GET /api/v1/validation/runs`
Lists historical validation runs.

### `GET /api/v1/validation/runs/{run_id}`
Returns detailed results and rule evidence for a specific run ID.

---

## 4. Fault Injection

### `POST /api/v1/faults/inject`
Injects controlled synthetic anomalies into a baseline dataset.

**Request Body**:
```json
{
  "base_dataset": "normal_run.csv",
  "fault_type": "ROTOR_OVERSPEED",
  "start_time": 20.0,
  "duration": 10.0,
  "severity": 1.2,
  "channel": "rotor_speed_rpm"
}
```

---

## 5. Certification Reports

### `GET /api/v1/reports/{run_id}`
Compiles or retrieves report metadata for a completed run.

### `GET /api/v1/reports/{run_id}/pdf`
Downloads compiled certification audit PDF.

### `GET /api/v1/reports/{run_id}/tex`
Downloads raw LaTeX source code (`.tex`).

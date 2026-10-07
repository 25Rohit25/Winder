"""Integration test suite for FastAPI REST endpoints using TestClient."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_api_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "turbine_model" in data


def test_api_list_datasets():
    resp = client.get("/api/v1/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    names = [d["filename"] for d in datasets]
    assert "normal_run.csv" in names


def test_api_get_telemetry():
    resp = client.get("/api/v1/datasets/normal_run.csv/telemetry?downsample=5")
    assert resp.status_code == 200
    res = resp.json()
    assert res["filename"] == "normal_run.csv"
    assert "data" in res
    assert len(res["data"]) > 0


def test_api_execute_validation_run():
    payload = {"dataset_name": "normal_run.csv", "scenario_type": "unit_test_run"}
    resp = client.post("/api/v1/validation/run", json=payload)
    assert resp.status_code == 200
    run_summary = resp.json()
    assert run_summary["dataset_name"] == "normal_run.csv"
    assert run_summary["overall_status"] == "PASS"
    assert run_summary["validation_score"] >= 90.0

    # Verify run is in run list
    run_id = run_summary["run_id"]
    get_run = client.get(f"/api/v1/validation/runs/{run_id}")
    assert get_run.status_code == 200
    assert get_run.json()["run_id"] == run_id


def test_api_generate_report_metadata():
    # First execute validation
    val_resp = client.post("/api/v1/validation/run", json={"dataset_name": "normal_run.csv"})
    run_id = val_resp.json()["run_id"]

    # Now request report
    rep_resp = client.get(f"/api/v1/reports/{run_id}")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["run_id"] == run_id
    assert rep_data["pdf_generated"] is True

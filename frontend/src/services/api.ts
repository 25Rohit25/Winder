import { DatasetMetadata, ReportMetadata, SystemHealth, TelemetryStreamResponse, ValidationRunSummary } from '../types';

const API_BASE = '/api/v1';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to retrieve system health');
  return res.json();
}

export async function fetchDatasets(): Promise<DatasetMetadata[]> {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) throw new Error('Failed to fetch telemetry datasets');
  return res.json();
}

export async function fetchTelemetry(filename: string, downsample: number = 2): Promise<TelemetryStreamResponse> {
  const res = await fetch(`${API_BASE}/datasets/${filename}/telemetry?downsample=${downsample}`);
  if (!res.ok) throw new Error(`Failed to load telemetry stream for ${filename}`);
  return res.json();
}

export async function executeValidationRun(datasetName: string, scenarioType?: string): Promise<ValidationRunSummary> {
  const res = await fetch(`${API_BASE}/validation/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_name: datasetName, scenario_type: scenarioType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Validation execution failed');
  }
  return res.json();
}

export async function fetchValidationRuns(): Promise<ValidationRunSummary[]> {
  const res = await fetch(`${API_BASE}/validation/runs`);
  if (!res.ok) throw new Error('Failed to fetch validation run history');
  return res.json();
}

export async function fetchRunById(runId: string): Promise<ValidationRunSummary> {
  const res = await fetch(`${API_BASE}/validation/runs/${runId}`);
  if (!res.ok) throw new Error(`Run ${runId} not found`);
  return res.json();
}

export async function fetchReport(runId: string): Promise<ReportMetadata> {
  const res = await fetch(`${API_BASE}/reports/${runId}`);
  if (!res.ok) throw new Error('Failed to compile or retrieve report');
  return res.json();
}

export async function injectSyntheticFault(
  baseDataset: string,
  faultType: string,
  startTime: number,
  duration: number,
  severity: number,
  channel: string
): Promise<DatasetMetadata> {
  const res = await fetch(`${API_BASE}/faults/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      base_dataset: baseDataset,
      fault_type: faultType,
      start_time: startTime,
      duration: duration,
      severity: severity,
      channel: channel,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Fault injection failed');
  }
  return res.json();
}

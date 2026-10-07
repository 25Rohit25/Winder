export type ValidationStatus = 'PASS' | 'WARNING' | 'FAIL';

export interface ValidationEvidence {
  validator: string;
  status: ValidationStatus;
  metric: string;
  actual: number | string | null;
  threshold: number | string | null;
  message: string;
  timestamp_range?: [number, number] | null;
  severity: string;
  details?: Record<string, any>;
}

export interface ValidationRunSummary {
  run_id: string;
  dataset_name: string;
  scenario_type: string;
  timestamp: string;
  overall_status: ValidationStatus;
  validation_score: number;
  total_tests: number;
  passed_count: number;
  warning_count: number;
  failed_count: number;
  detection_rate_pct: number;
  false_positive_rate_pct: number;
  max_rotor_speed_rpm: number;
  max_generator_torque_nm: number;
  max_electrical_power_kw: number;
  max_power_deviation_pct: number;
  pitch_response_time_sec: number;
  max_yaw_error_deg: number;
  signal_completeness_pct: number;
  execution_duration_ms: number;
  results: ValidationEvidence[];
}

export interface DatasetMetadata {
  dataset_id: string;
  filename: string;
  scenario_type: string;
  sample_count: number;
  duration_sec: number;
  sampling_rate_hz: number;
  time_step_sec: number;
  start_time: number;
  end_time: number;
  columns: string[];
  summary_stats?: Record<string, Record<string, number>>;
  created_at: string;
}

export interface TelemetryStreamResponse {
  filename: string;
  sample_count: number;
  columns: string[];
  data: Array<{
    timestamp: number;
    wind_speed_mps: number;
    rotor_speed_rpm: number;
    generator_speed_rpm: number;
    generator_torque_nm: number;
    blade_pitch_deg: number;
    electrical_power_kw: number;
    tower_acceleration: number;
    nacelle_yaw_error: number;
    controller_state: string;
    fault_flags: number;
  }>;
}

export interface ReportMetadata {
  report_id: string;
  run_id: string;
  dataset_name: string;
  created_at: string;
  tex_path: string;
  pdf_path?: string | null;
  pdf_generated: boolean;
  engine_used: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  python_version: string;
  turbine_model: string;
  diagnostics: Record<string, boolean>;
}

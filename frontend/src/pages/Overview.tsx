import React, { useEffect, useState } from 'react';
import { Play, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { TelemetryChart } from '../components/TelemetryChart';
import { executeValidationRun, fetchDatasets, fetchTelemetry, fetchValidationRuns } from '../services/api';
import { DatasetMetadata, TelemetryStreamResponse, ValidationRunSummary } from '../types';

export const Overview: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>('normal_run.csv');
  const [latestRun, setLatestRun] = useState<ValidationRunSummary | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryStreamResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dsets, runs] = await Promise.all([
        fetchDatasets(),
        fetchValidationRuns(),
      ]);
      setDatasets(dsets);

      let currentRun = runs.length > 0 ? runs[0] : null;

      // If no run exists, trigger initial run on first dataset
      if (!currentRun && dsets.length > 0) {
        currentRun = await executeValidationRun(dsets[0].filename);
      }

      if (currentRun) {
        setLatestRun(currentRun);
        setSelectedDataset(currentRun.dataset_name);
        const telem = await fetchTelemetry(currentRun.dataset_name, 2);
        setTelemetry(telem);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load platform data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleRunValidation = async () => {
    try {
      setRunning(true);
      setError(null);
      const run = await executeValidationRun(selectedDataset);
      setLatestRun(run);
      const telem = await fetchTelemetry(selectedDataset, 2);
      setTelemetry(telem);
    } catch (err: any) {
      setError(err.message || 'Execution failed');
    } finally {
      setRunning(false);
    }
  };

  const handleDatasetChange = async (filename: string) => {
    setSelectedDataset(filename);
    try {
      setLoading(true);
      const telem = await fetchTelemetry(filename, 2);
      setTelemetry(telem);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !latestRun) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw size={28} className="animate-spin text-industrial-teal" />
        <span className="text-sm font-medium text-slate-500">Ingesting turbine telemetry & initializing validation engine...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Controls Toolbar */}
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight">Supervisory Control Validation Overview</h1>
          <p className="text-xs text-slate-500">
            NREL 5MW Baseline Wind Turbine &bull; IEC 61400-1 ed.4 Standard Verification Suite
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-600">Telemetry Dataset:</label>
            <select
              value={selectedDataset}
              onChange={(e) => handleDatasetChange(e.target.value)}
              className="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs font-mono font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-industrial-teal"
            >
              {datasets.map((d) => (
                <option key={d.filename} value={d.filename}>
                  {d.filename} ({d.scenario_type})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRunValidation}
            disabled={running}
            className="flex items-center gap-1.5 bg-industrial-teal hover:bg-industrial-tealHover text-white px-4 py-1.5 rounded text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            {running ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            <span>{running ? 'Executing...' : 'Run Validation'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-md text-xs flex items-center gap-2">
          <AlertCircle size={16} className="text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Validation Status Banner */}
      {latestRun && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Overall Score Banner */}
          <div className="bg-industrial-navy text-white rounded-md p-5 shadow-sm col-span-1 md:col-span-1 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-300 uppercase">Audit Score</span>
              <StatusBadge status={latestRun.overall_status} size="sm" />
            </div>
            <div className="my-3">
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold font-mono">{latestRun.validation_score}</span>
                <span className="text-sm text-slate-300">/ 100</span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                {latestRun.passed_count} Passed &bull; {latestRun.warning_count} Warnings &bull; {latestRun.failed_count} Failed
              </p>
            </div>
            <div className="text-[11px] text-slate-400 border-t border-slate-700/60 pt-2 flex items-center justify-between font-mono">
              <span>Run: {latestRun.run_id}</span>
              <span className="flex items-center gap-1">
                <Clock size={11} /> {latestRun.execution_duration_ms}ms
              </span>
            </div>
          </div>

          {/* Quick Metrics */}
          <MetricCard
            title="Max Rotor Speed"
            value={latestRun.max_rotor_speed_rpm}
            unit="RPM"
            limit="15.00 RPM"
            status={latestRun.max_rotor_speed_rpm > 15.0 ? 'critical' : (latestRun.max_rotor_speed_rpm > 14.5 ? 'warning' : 'nominal')}
            subtitle="Low-speed shaft overspeed ceiling"
          />

          <MetricCard
            title="Max Power Deviation"
            value={`${latestRun.max_power_deviation_pct}%`}
            limit="10.0%"
            status={latestRun.max_power_deviation_pct > 10.0 ? 'critical' : 'nominal'}
            subtitle={`Rated Yield: ${latestRun.max_electrical_power_kw} kW`}
          />

          <MetricCard
            title="Signal Completeness"
            value={`${latestRun.signal_completeness_pct}%`}
            limit="99.0%"
            status={latestRun.signal_completeness_pct < 99.0 ? 'critical' : 'nominal'}
            subtitle={`Detection Rate: ${latestRun.detection_rate_pct}%`}
          />
        </div>
      )}

      {/* Engineering Telemetry Charts Grid */}
      {telemetry && telemetry.data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Chart 1: Wind Speed */}
          <TelemetryChart
            title="Effective Hub-Height Wind Speed"
            data={telemetry.data}
            lines={[
              { key: 'wind_speed_mps', name: 'Wind Speed', color: '#0284c7', unit: 'm/s' },
            ]}
            referenceLines={[
              { y: 11.4, label: 'Rated Wind (11.4 m/s)', color: '#dc2626' },
              { y: 3.0, label: 'Cut-In (3.0 m/s)', color: '#475569' },
            ]}
            yAxisUnit=" m/s"
          />

          {/* Chart 2: Drivetrain Kinematics */}
          <TelemetryChart
            title="Drivetrain Kinematics (Rotor & Generator Velocity)"
            data={telemetry.data}
            lines={[
              { key: 'rotor_speed_rpm', name: 'Rotor Speed', color: '#16a34a', unit: 'RPM', yAxisId: 'left' },
              { key: 'generator_speed_rpm', name: 'Generator Speed', color: '#ea580c', unit: 'RPM', yAxisId: 'right' },
            ]}
            referenceLines={[
              { y: 15.0, label: 'Trip Limit (15.0 RPM)', color: '#dc2626', yAxisId: 'left' },
              { y: 12.1, label: 'Rated Rotor (12.1 RPM)', color: '#64748b', yAxisId: 'left' },
            ]}
            yAxisLabel="Rotor [RPM]"
            secondaryYAxisLabel="Gen [RPM]"
          />

          {/* Chart 3: Blade Pitch Control */}
          <TelemetryChart
            title="Collective Blade Pitch Angle Response"
            data={telemetry.data}
            lines={[
              { key: 'blade_pitch_deg', name: 'Blade Pitch', color: '#9333ea', unit: 'deg' },
            ]}
            referenceLines={[
              { y: 0.0, label: 'Fine Pitch (0 deg)', color: '#64748b' },
              { y: 90.0, label: 'Feather Stop (90 deg)', color: '#dc2626' },
            ]}
            yAxisUnit=" deg"
          />

          {/* Chart 4: Generator Electromagnetic Torque */}
          <TelemetryChart
            title="Generator Torque Demand"
            data={telemetry.data}
            lines={[
              { key: 'generator_torque_nm', name: 'Electromagnetic Torque', color: '#007299', unit: 'Nm' },
            ]}
            referenceLines={[
              { y: 43093.55, label: 'Rated Torque (43.1 kNm)', color: '#475569' },
              { y: 47402.91, label: 'Overload Trip (47.4 kNm)', color: '#dc2626' },
            ]}
            yAxisUnit=" Nm"
          />

          {/* Chart 5: Active Electrical Power */}
          <TelemetryChart
            title="Active 3-Phase Grid Power Yield"
            data={telemetry.data}
            lines={[
              { key: 'electrical_power_kw', name: 'Active Power', color: '#0d9488', unit: 'kW' },
            ]}
            referenceLines={[
              { y: 5000.0, label: 'Rated Capacity (5000 kW)', color: '#dc2626' },
            ]}
            yAxisUnit=" kW"
          />

          {/* Chart 6: Nacelle Yaw Alignment Tracking */}
          <TelemetryChart
            title="Nacelle Wind Alignment Tracking Error"
            data={telemetry.data}
            lines={[
              { key: 'nacelle_yaw_error', name: 'Yaw Misalignment', color: '#e11d48', unit: 'deg' },
            ]}
            referenceLines={[
              { y: 10.0, label: '+10 deg Threshold', color: '#f59e0b' },
              { y: -10.0, label: '-10 deg Threshold', color: '#f59e0b' },
            ]}
            yAxisUnit=" deg"
          />
        </div>
      )}
    </div>
  );
};

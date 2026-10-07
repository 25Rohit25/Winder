import React, { useEffect, useState } from 'react';
import { Database, Filter, Download, RefreshCw, Eye } from 'lucide-react';
import { TelemetryChart } from '../components/TelemetryChart';
import { fetchDatasets, fetchTelemetry } from '../services/api';
import { DatasetMetadata, TelemetryStreamResponse } from '../types';

export const SignalExplorer: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('normal_run.csv');
  const [downsample, setDownsample] = useState<number>(2);
  const [telemetry, setTelemetry] = useState<TelemetryStreamResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Active channel toggles
  const [activeChannels, setActiveChannels] = useState<{ [key: string]: boolean }>({
    wind_speed_mps: true,
    rotor_speed_rpm: true,
    generator_speed_rpm: false,
    generator_torque_nm: false,
    blade_pitch_deg: true,
    electrical_power_kw: true,
    tower_acceleration: false,
    nacelle_yaw_error: false,
  });

  const channelConfig = [
    { key: 'wind_speed_mps', label: 'Wind Speed', unit: 'm/s', color: '#0284c7' },
    { key: 'rotor_speed_rpm', label: 'Rotor Speed', unit: 'RPM', color: '#16a34a' },
    { key: 'generator_speed_rpm', label: 'Generator Speed', unit: 'RPM', color: '#ea580c' },
    { key: 'generator_torque_nm', label: 'Generator Torque', unit: 'Nm', color: '#007299' },
    { key: 'blade_pitch_deg', label: 'Blade Pitch', unit: 'deg', color: '#9333ea' },
    { key: 'electrical_power_kw', label: 'Electrical Power', unit: 'kW', color: '#0d9488' },
    { key: 'tower_acceleration', label: 'Tower Accel', unit: 'm/s²', color: '#e11d48' },
    { key: 'nacelle_yaw_error', label: 'Nacelle Yaw Error', unit: 'deg', color: '#d97706' },
  ];

  const loadData = async (filename: string, stride: number) => {
    try {
      setLoading(true);
      const [dsets, telem] = await Promise.all([
        datasets.length === 0 ? fetchDatasets() : Promise.resolve(datasets),
        fetchTelemetry(filename, stride),
      ]);
      if (datasets.length === 0) setDatasets(dsets);
      setTelemetry(telem);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedFile, downsample);
  }, [selectedFile, downsample]);

  const toggleChannel = (key: string) => {
    setActiveChannels((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const selectedLines = channelConfig
    .filter((c) => activeChannels[c.key])
    .map((c) => ({
      key: c.key,
      name: `${c.label} (${c.unit})`,
      color: c.color,
      unit: c.unit,
    }));

  return (
    <div className="space-y-6">
      {/* Header & Controls Toolbar */}
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Database size={18} className="text-industrial-teal" />
            High-Resolution Signal Explorer
          </h1>
          <p className="text-xs text-slate-500">
            Multi-channel SCADA & simulation telemetry analysis with point-by-point inspection
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600">Dataset:</span>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs font-mono font-medium text-slate-800"
            >
              {datasets.map((d) => (
                <option key={d.filename} value={d.filename}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600">Sampling:</span>
            <select
              value={downsample}
              onChange={(e) => setDownsample(Number(e.target.value))}
              className="bg-slate-50 border border-slate-300 rounded px-2.5 py-1.5 text-xs font-mono text-slate-800"
            >
              <option value={1}>1x (Full 20 Hz)</option>
              <option value={2}>2x (10 Hz)</option>
              <option value={5}>5x (4 Hz)</option>
              <option value={10}>10x (2 Hz)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Channel Toggles Bar */}
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          <Filter size={13} />
          <span>Active Telemetry Channels (Toggle to View/Hide):</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {channelConfig.map((ch) => {
            const active = activeChannels[ch.key];
            return (
              <button
                key={ch.key}
                onClick={() => toggleChannel(ch.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                  active
                    ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: ch.color }}
                />
                <span>{ch.label}</span>
                <span className="text-[10px] opacity-75 font-mono">[{ch.unit}]</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Master Interactive Chart */}
      {loading ? (
        <div className="flex items-center justify-center p-12 bg-white rounded-md border border-slate-200">
          <RefreshCw size={24} className="animate-spin text-industrial-teal" />
          <span className="ml-2 text-xs text-slate-500">Loading stream points...</span>
        </div>
      ) : (
        telemetry && telemetry.data && (
          <TelemetryChart
            title={`Telemetry Trace: ${selectedFile} (${telemetry.sample_count} points)`}
            data={telemetry.data}
            lines={selectedLines}
            height={360}
          />
        )
      )}

      {/* Raw Data Preview Table */}
      {telemetry && telemetry.data && (
        <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Eye size={14} className="text-industrial-teal" />
              Raw Time-Series Frame Samples (Top 10 Rows)
            </h3>
            <span className="text-xs text-slate-400 font-mono">Total Points: {telemetry.sample_count}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs font-mono">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  {telemetry.columns.map((c) => (
                    <th key={c} className="py-2 px-3 font-semibold">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {telemetry.data.slice(0, 10).map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80">
                    {telemetry.columns.map((c) => (
                      <td key={c} className="py-1.5 px-3 text-slate-700 whitespace-nowrap">
                        {typeof (row as any)[c] === 'number'
                          ? Number((row as any)[c]).toFixed(3)
                          : String((row as any)[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

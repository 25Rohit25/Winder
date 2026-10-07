import React, { useEffect, useState } from 'react';
import { Flame, Play, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import { executeValidationRun, fetchDatasets, injectSyntheticFault } from '../services/api';
import { DatasetMetadata, ValidationRunSummary } from '../types';

interface FaultInjectionProps {
  onRunCompleted: (run: ValidationRunSummary) => void;
}

export const FaultInjection: React.FC<FaultInjectionProps> = ({ onRunCompleted }) => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [baseDataset, setBaseDataset] = useState<string>('normal_run.csv');
  const [faultType, setFaultType] = useState<string>('ROTOR_OVERSPEED');
  const [startTime, setStartTime] = useState<number>(20.0);
  const [duration, setDuration] = useState<number>(10.0);
  const [severity, setSeverity] = useState<number>(1.2);
  const [channel, setChannel] = useState<string>('rotor_speed_rpm');

  const [injecting, setInjecting] = useState<boolean>(false);
  const [resultDataset, setResultDataset] = useState<DatasetMetadata | null>(null);
  const [resultSummary, setResultSummary] = useState<ValidationRunSummary | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const faultCatalog = [
    {
      type: 'ROTOR_OVERSPEED',
      name: 'Rotor Aerodynamic Overspeed',
      description: 'Forces rotor rotational acceleration past 15.0 RPM certified safety ceiling.',
      channel: 'rotor_speed_rpm',
      expectedOutcome: 'FAIL verdict by overspeed trip validator & emergency trip state verification.',
    },
    {
      type: 'PITCH_ACTUATOR_DELAY',
      name: 'Pitch Actuator Sluggishness / Lag',
      description: 'Injects 3.0s transport delay & prevents prompt pitch shedding above rated wind.',
      channel: 'blade_pitch_deg',
      expectedOutcome: 'WARNING/FAIL by pitch response validator & actuator rate monitor.',
    },
    {
      type: 'SENSOR_DROPOUT',
      name: 'Generator Speed Sensor Dropout',
      description: 'Replaces telemetry stream with missing NaN values across fault window.',
      channel: 'generator_speed_rpm',
      expectedOutcome: 'FAIL verdict by signal integrity NaN dropout validator.',
    },
    {
      type: 'SENSOR_FREEZE',
      name: 'Anemometer Sensor Freeze',
      description: 'Sticks wind speed sensor to static frozen constant value.',
      channel: 'wind_speed_mps',
      expectedOutcome: 'FAIL verdict by zero-variance sensor freeze detector.',
    },
    {
      type: 'TORQUE_SPIKE',
      name: 'Converter Torque Transient Spike',
      description: 'Injects sudden step change of +14,000 Nm on generator converter.',
      channel: 'generator_torque_nm',
      expectedOutcome: 'FAIL verdict by converter torque rate-of-change & spike detector.',
    },
    {
      type: 'YAW_MISALIGNMENT',
      name: 'Severe Nacelle Yaw Misalignment',
      description: 'Offsets nacelle orientation by +16 degrees relative to wind vector.',
      channel: 'nacelle_yaw_error',
      expectedOutcome: 'FAIL verdict by nacelle peak & persistent yaw misalignment validator.',
    },
    {
      type: 'POWER_UNDERPERFORMANCE',
      name: 'Turbine Electrical Underperformance',
      description: 'Derates generator power yield by 40% below IEC 61400-12 reference.',
      channel: 'electrical_power_kw',
      expectedOutcome: 'FAIL verdict by IEC 61400-12 power curve deviation validator.',
    },
  ];

  useEffect(() => {
    fetchDatasets().then(setDatasets).catch(console.error);
  }, []);

  const handleFaultSelect = (type: string) => {
    setFaultType(type);
    const item = faultCatalog.find((f) => f.type === type);
    if (item) setChannel(item.channel);
  };

  const handleInjectAndValidate = async () => {
    try {
      setInjecting(true);
      setStatusMsg('Injecting controlled synthetic anomaly into telemetry stream...');
      const createdDataset = await injectSyntheticFault(
        baseDataset,
        faultType,
        startTime,
        duration,
        severity,
        channel
      );
      setResultDataset(createdDataset);

      setStatusMsg('Executing automated validation pipeline on faulted dataset...');
      const summary = await executeValidationRun(createdDataset.filename, `fault_${faultType.toLowerCase()}`);
      setResultSummary(summary);
      onRunCompleted(summary);
      setStatusMsg(null);
    } catch (err: any) {
      alert(`Fault Injection Failed: ${err.message}`);
    } finally {
      setInjecting(false);
    }
  };

  const currentFaultInfo = faultCatalog.find((f) => f.type === faultType) || faultCatalog[0];

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm">
        <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Flame size={18} className="text-rose-600" />
          Controlled Synthetic Fault Injection Workbench
        </h1>
        <p className="text-xs text-slate-500">
          Inject physics-based actuator delays, overspeed events, and sensor failures to verify controller protection rules
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Fault Selection Catalog */}
        <div className="bg-white border border-slate-200 rounded-md p-5 shadow-sm space-y-4 col-span-1">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            1. Select Fault Model
          </h2>
          <div className="space-y-2">
            {faultCatalog.map((f) => (
              <button
                key={f.type}
                onClick={() => handleFaultSelect(f.type)}
                className={`w-full text-left p-3 rounded-md border text-xs transition-all ${
                  faultType === f.type
                    ? 'border-industrial-teal bg-sky-50/60 shadow-sm'
                    : 'border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="font-bold text-slate-800">{f.name}</div>
                <div className="text-[11px] text-slate-500 mt-1 line-clamp-2">{f.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Center Column: Fault Configuration Form */}
        <div className="bg-white border border-slate-200 rounded-md p-5 shadow-sm space-y-5 col-span-1 lg:col-span-2">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            2. Configure Injection Parameters
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-medium text-slate-700">
            <div>
              <label className="block text-slate-500 mb-1">Source Baseline Telemetry:</label>
              <select
                value={baseDataset}
                onChange={(e) => setBaseDataset(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono"
              >
                {datasets.map((d) => (
                  <option key={d.filename} value={d.filename}>
                    {d.filename}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-500 mb-1">Target Channel:</label>
              <input
                type="text"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-500 mb-1">Start Time (seconds):</label>
              <input
                type="number"
                step="1.0"
                value={startTime}
                onChange={(e) => setStartTime(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-500 mb-1">Duration (seconds):</label>
              <input
                type="number"
                step="1.0"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded px-3 py-2 text-xs font-mono"
              />
            </div>

            <div className="sm:col-span-2">
              <div className="flex justify-between text-slate-500 mb-1">
                <span>Severity Multiplier:</span>
                <span className="font-mono font-bold text-slate-800">{severity.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                className="w-full accent-industrial-teal cursor-pointer"
              />
            </div>
          </div>

          {/* Diagnostic Prediction Box */}
          <div className="bg-slate-50 border border-slate-200 rounded p-4 text-xs space-y-1.5">
            <div className="font-bold text-slate-800 flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-industrial-teal" />
              Expected Protective Action:
            </div>
            <p className="text-slate-600">{currentFaultInfo.expectedOutcome}</p>
          </div>

          <button
            onClick={handleInjectAndValidate}
            disabled={injecting}
            className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-2.5 rounded-md text-xs shadow-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
          >
            <Play size={14} />
            <span>{injecting ? statusMsg || 'Injecting & Validating...' : 'Inject Fault & Verify Detection'}</span>
          </button>

          {/* Validation Result Feedback */}
          {resultSummary && (
            <div className="mt-4 border border-slate-200 rounded p-4 bg-white shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">
                  Detection Result: {resultSummary.run_id}
                </span>
                <span
                  className={`text-xs font-bold px-2.5 py-0.5 rounded ${
                    resultSummary.failed_count > 0 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {resultSummary.failed_count > 0 ? 'FAULT SUCCESSFULLY DETECTED' : 'UNCAUGHT / MARGINAL'}
                </span>
              </div>
              <p className="text-xs text-slate-600">
                Generated Dataset: <span className="font-mono text-industrial-teal">{resultDataset?.filename}</span> &bull;
                Verdict: <span className="font-bold">{resultSummary.overall_status}</span> &bull;
                Failures Logged: <span className="font-bold text-rose-600">{resultSummary.failed_count}</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Server, CheckCircle2, Cpu, HardDrive, ShieldCheck, RefreshCw } from 'lucide-react';
import { fetchHealth } from '../services/api';
import { SystemHealth as ISystemHealth } from '../types';

export const SystemHealth: React.FC = () => {
  const [health, setHealth] = useState<ISystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadHealth = async () => {
    try {
      setLoading(true);
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Server size={18} className="text-industrial-teal" />
            System Diagnostics & Health Probes
          </h1>
          <p className="text-xs text-slate-500">
            Runtime environment status, turbine model specification, and subsystem readiness checks
          </p>
        </div>
        <button
          onClick={loadHealth}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded transition-colors"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Ping API</span>
        </button>
      </div>

      {health && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Environment Specs */}
          <div className="bg-white border border-slate-200 rounded-md p-5 shadow-sm space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Cpu size={14} className="text-industrial-teal" />
              Runtime Architecture
            </h2>
            <div className="divide-y divide-slate-100 text-xs">
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-medium">Service Name:</span>
                <span className="font-mono font-bold text-slate-800">{health.app_name}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-medium">Release Version:</span>
                <span className="font-mono text-slate-800">v{health.version}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-medium">Environment:</span>
                <span className="font-mono text-slate-800 uppercase">{health.environment}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-medium">Python Runtime:</span>
                <span className="font-mono text-slate-800">{health.python_version}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-medium">Status Verdict:</span>
                <span className="text-emerald-600 font-bold flex items-center gap-1">
                  <CheckCircle2 size={13} /> {health.status.toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Turbine Model Baseline Specs */}
          <div className="bg-white border border-slate-200 rounded-md p-5 shadow-sm space-y-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-industrial-teal" />
              NREL 5MW Baseline Physical Envelope
            </h2>
            <div className="divide-y divide-slate-100 text-xs font-mono">
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-sans">Rated Power:</span>
                <span className="font-bold text-slate-800">5,000.0 kW (5.0 MW)</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-sans">Rated Rotor Speed:</span>
                <span className="text-slate-800">12.10 RPM</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-sans">Emergency Trip Limit:</span>
                <span className="text-rose-600 font-bold">15.00 RPM</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-sans">Drivetrain Ratio:</span>
                <span className="text-slate-800">1 : 97.0</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-sans">Rated Generator Torque:</span>
                <span className="text-slate-800">43,093.55 Nm</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-slate-500 font-sans">Max Pitch Rate:</span>
                <span className="text-slate-800">8.00 deg/s</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

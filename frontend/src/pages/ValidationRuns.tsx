import React, { useEffect, useState } from 'react';
import { Layers, RefreshCw, FileText, ExternalLink, Clock } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { fetchValidationRuns } from '../services/api';
import { ValidationRunSummary } from '../types';

interface ValidationRunsProps {
  onSelectRun: (runId: string) => void;
  onNavigateReports: (runId: string) => void;
}

export const ValidationRuns: React.FC<ValidationRunsProps> = ({ onSelectRun, onNavigateReports }) => {
  const [runs, setRuns] = useState<ValidationRunSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadRuns = async () => {
    try {
      setLoading(true);
      const data = await fetchValidationRuns();
      setRuns(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Layers size={18} className="text-industrial-teal" />
            Validation Run Registry
          </h1>
          <p className="text-xs text-slate-500">
            Historical audit log of automated turbine controller verification executions
          </p>
        </div>
        <button
          onClick={loadRuns}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded transition-colors"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-md shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Run ID</th>
                <th className="py-2.5 px-4 font-semibold">Dataset / Scenario</th>
                <th className="py-2.5 px-4 font-semibold">Verdict</th>
                <th className="py-2.5 px-4 font-semibold">Score</th>
                <th className="py-2.5 px-4 font-semibold">Tests (P/W/F)</th>
                <th className="py-2.5 px-4 font-semibold">Max Rotor</th>
                <th className="py-2.5 px-4 font-semibold">Exec Duration</th>
                <th className="py-2.5 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400 font-sans">
                    No validation runs logged yet. Execute a validation run from the Overview dashboard.
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-bold text-industrial-teal">
                      {r.run_id}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-800">{r.dataset_name}</div>
                      <div className="text-[10px] text-slate-400">{r.scenario_type}</div>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={r.overall_status} size="sm" />
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-800 text-sm">{r.validation_score}</span>
                      <span className="text-[10px] text-slate-400">/100</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-emerald-600 font-semibold">{r.passed_count}</span> /{' '}
                      <span className="text-amber-600 font-semibold">{r.warning_count}</span> /{' '}
                      <span className="text-rose-600 font-semibold">{r.failed_count}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-700">
                      {r.max_rotor_speed_rpm.toFixed(2)} RPM
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      <span className="flex items-center gap-1">
                        <Clock size={11} /> {r.execution_duration_ms.toFixed(1)}ms
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => onSelectRun(r.run_id)}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 hover:text-industrial-teal bg-slate-50 hover:bg-slate-100 border border-slate-200 px-2 py-1 rounded"
                      >
                        <ExternalLink size={12} />
                        <span>Evidence</span>
                      </button>
                      <button
                        onClick={() => onNavigateReports(r.run_id)}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-industrial-teal hover:text-industrial-tealHover bg-sky-50 border border-sky-200 px-2 py-1 rounded"
                      >
                        <FileText size={12} />
                        <span>Report</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

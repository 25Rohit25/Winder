import React, { useEffect, useState } from 'react';
import { CheckSquare, Search, Filter, AlertCircle, ShieldAlert } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { fetchRunById, fetchValidationRuns } from '../services/api';
import { ValidationEvidence, ValidationRunSummary, ValidationStatus } from '../types';

interface TestResultsProps {
  initialRunId?: string;
}

export const TestResults: React.FC<TestResultsProps> = ({ initialRunId }) => {
  const [runs, setRuns] = useState<ValidationRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>(initialRunId || '');
  const [runSummary, setRunSummary] = useState<ValidationRunSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const allRuns = await fetchValidationRuns();
        setRuns(allRuns);
        const targetId = initialRunId || (allRuns.length > 0 ? allRuns[0].run_id : '');
        setSelectedRunId(targetId);
        if (targetId) {
          const summary = await fetchRunById(targetId);
          setRunSummary(summary);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [initialRunId]);

  const handleRunChange = async (runId: string) => {
    setSelectedRunId(runId);
    try {
      setLoading(true);
      const summary = await fetchRunById(runId);
      setRunSummary(summary);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredResults = (runSummary?.results || []).filter((r) => {
    if (statusFilter !== 'ALL' && r.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        r.validator.toLowerCase().includes(q) ||
        r.metric.toLowerCase().includes(q) ||
        r.message.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header Toolbar */}
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <CheckSquare size={18} className="text-industrial-teal" />
            Detailed Test Evidence Matrix
          </h1>
          <p className="text-xs text-slate-500">
            Rule-by-rule deterministic compliance verification, threshold audits, and failure diagnostics
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-600">Select Run:</span>
          <select
            value={selectedRunId}
            onChange={(e) => handleRunChange(e.target.value)}
            className="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs font-mono font-medium text-slate-800"
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} &bull; {r.dataset_name} ({r.overall_status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search validator, metric, or finding..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded pl-9 pr-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-industrial-teal"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          {['ALL', 'PASS', 'WARNING', 'FAIL'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded text-xs font-semibold border transition-all ${
                statusFilter === st
                  ? 'bg-industrial-navy text-white border-industrial-navy shadow-sm'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Evidence Table */}
      <div className="bg-white border border-slate-200 rounded-md shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Validator Rule</th>
                <th className="py-2.5 px-4 font-semibold">Status</th>
                <th className="py-2.5 px-4 font-semibold">Metric</th>
                <th className="py-2.5 px-4 font-semibold">Observed Actual</th>
                <th className="py-2.5 px-4 font-semibold">Acceptance Threshold</th>
                <th className="py-2.5 px-4 font-semibold">Diagnostic Finding</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredResults.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                    No validation rules matched the filter criteria.
                  </td>
                </tr>
              ) : (
                filteredResults.map((ev, idx) => (
                  <tr
                    key={idx}
                    className={`hover:bg-slate-50/80 transition-colors ${
                      ev.status === 'FAIL'
                        ? 'bg-rose-50/30'
                        : ev.status === 'WARNING'
                        ? 'bg-amber-50/20'
                        : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-bold text-slate-800">
                      {ev.validator}
                      {ev.severity === 'CRITICAL' && (
                        <span className="ml-1.5 bg-rose-100 text-rose-800 text-[9px] px-1 py-0.5 rounded font-bold">
                          CRITICAL
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={ev.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-slate-700 font-semibold">{ev.metric}</td>
                    <td className="py-3 px-4 text-slate-900 font-bold">
                      {typeof ev.actual === 'number' ? ev.actual.toFixed(2) : String(ev.actual)}
                    </td>
                    <td className="py-3 px-4 text-slate-500">{String(ev.threshold)}</td>
                    <td className="py-3 px-4 text-slate-700 font-sans text-xs">
                      {ev.message}
                      {ev.timestamp_range && (
                        <span className="block text-[11px] font-mono text-slate-400 mt-0.5">
                          Window: [{ev.timestamp_range[0].toFixed(1)}s - {ev.timestamp_range[1].toFixed(1)}s]
                        </span>
                      )}
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

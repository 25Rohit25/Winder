import React, { useEffect, useState } from 'react';
import { FileText, Download, Code, CheckCircle, RefreshCw } from 'lucide-react';
import { fetchReport, fetchValidationRuns } from '../services/api';
import { ReportMetadata, ValidationRunSummary } from '../types';

interface ReportsProps {
  initialRunId?: string;
}

export const Reports: React.FC<ReportsProps> = ({ initialRunId }) => {
  const [runs, setRuns] = useState<ValidationRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>(initialRunId || '');
  const [reportMeta, setReportMeta] = useState<ReportMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [compiling, setCompiling] = useState<boolean>(false);

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        const allRuns = await fetchValidationRuns();
        setRuns(allRuns);
        const targetId = initialRunId || (allRuns.length > 0 ? allRuns[0].run_id : '');
        setSelectedRunId(targetId);
        if (targetId) {
          const meta = await fetchReport(targetId);
          setReportMeta(meta);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [initialRunId]);

  const handleSelectRun = async (runId: string) => {
    setSelectedRunId(runId);
    try {
      setCompiling(true);
      const meta = await fetchReport(runId);
      setReportMeta(meta);
    } catch (err) {
      console.error(err);
    } finally {
      setCompiling(false);
    }
  };

  const downloadPdf = () => {
    if (!selectedRunId) return;
    window.open(`/api/v1/reports/${selectedRunId}/pdf`, '_blank');
  };

  const downloadTex = () => {
    if (!selectedRunId) return;
    window.open(`/api/v1/reports/${selectedRunId}/tex`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FileText size={18} className="text-industrial-teal" />
            Automated Certification & Technical Audit Reports
          </h1>
          <p className="text-xs text-slate-500">
            Export formal IEC 61400-1 / GL guideline engineering compliance reports in PDF and LaTeX formats
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600">Select Audit Run:</span>
          <select
            value={selectedRunId}
            onChange={(e) => handleSelectRun(e.target.value)}
            className="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs font-mono font-medium text-slate-800"
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} ({r.dataset_name}) - {r.overall_status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {compiling ? (
        <div className="flex flex-col items-center justify-center p-16 bg-white rounded-md border border-slate-200 gap-2">
          <RefreshCw size={24} className="animate-spin text-industrial-teal" />
          <span className="text-xs font-medium text-slate-500">Compiling validation report artifacts...</span>
        </div>
      ) : (
        reportMeta && (
          <div className="bg-white border border-slate-200 rounded-md p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <span className="text-xs font-bold text-slate-400 font-mono uppercase tracking-wider">
                  Audit Certificate Document
                </span>
                <h2 className="text-base font-bold text-slate-800 mt-0.5">
                  Wind Turbine Controller Validation Report ({selectedRunId})
                </h2>
                <p className="text-xs text-slate-500 mt-1 font-mono">
                  Engine: {reportMeta.engine_used} &bull; Generated: {new Date(reportMeta.created_at).toLocaleString()}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={downloadPdf}
                  className="flex items-center gap-1.5 bg-industrial-teal hover:bg-industrial-tealHover text-white text-xs font-bold px-4 py-2 rounded-md shadow-sm transition-colors"
                >
                  <Download size={14} />
                  <span>Download PDF Report</span>
                </button>
                <button
                  onClick={downloadTex}
                  className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-4 py-2 rounded-md transition-colors border border-slate-200"
                >
                  <Code size={14} />
                  <span>Download LaTeX (.tex)</span>
                </button>
              </div>
            </div>

            {/* Document Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="bg-slate-50 p-3 rounded border border-slate-200">
                <span className="text-slate-400 font-sans block text-[11px]">Report Identifier</span>
                <span className="font-bold text-slate-800">{reportMeta.report_id}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded border border-slate-200">
                <span className="text-slate-400 font-sans block text-[11px]">PDF Status</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <CheckCircle size={13} /> {reportMeta.pdf_generated ? 'Compiled & Verified' : 'Source Only'}
                </span>
              </div>
              <div className="bg-slate-50 p-3 rounded border border-slate-200">
                <span className="text-slate-400 font-sans block text-[11px]">LaTeX Source File</span>
                <span className="text-slate-700 truncate block">{reportMeta.tex_path}</span>
              </div>
            </div>

            {/* Preview Banner */}
            <div className="bg-sky-50/60 border border-sky-200/80 rounded-md p-4 text-xs text-slate-700 flex items-start gap-3">
              <FileText size={20} className="text-industrial-teal shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 block mb-1">
                  Certification Document Contents
                </span>
                <p className="text-slate-600 leading-relaxed">
                  The document includes an executive summary, NREL 5MW turbine model specs, key physical telemetry KPIs,
                  a structured test-by-test rule verdict matrix, multi-panel telemetry plots, and formal engineering audit sign-off block.
                </p>
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
};

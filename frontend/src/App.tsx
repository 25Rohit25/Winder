import React, { useState, useEffect } from 'react';
import { Navbar, TabType } from './components/Navbar';
import { Overview } from './pages/Overview';
import { ValidationRuns } from './pages/ValidationRuns';
import { SignalExplorer } from './pages/SignalExplorer';
import { TestResults } from './pages/TestResults';
import { FaultInjection } from './pages/FaultInjection';
import { Reports } from './pages/Reports';
import { SystemHealth } from './pages/SystemHealth';
import { fetchHealth } from './services/api';
import { ValidationRunSummary } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [systemHealthy, setSystemHealthy] = useState<boolean>(true);

  useEffect(() => {
    fetchHealth()
      .then((h) => setSystemHealthy(h.status === 'healthy'))
      .catch(() => setSystemHealthy(false));
  }, []);

  const handleSelectRunForEvidence = (runId: string) => {
    setSelectedRunId(runId);
    setActiveTab('tests');
  };

  const handleSelectRunForReport = (runId: string) => {
    setSelectedRunId(runId);
    setActiveTab('reports');
  };

  const handleRunCompleted = (run: ValidationRunSummary) => {
    setSelectedRunId(run.run_id);
    setActiveTab('runs');
  };

  return (
    <div className="min-h-screen bg-industrial-surface flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        systemHealthy={systemHealthy}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <Overview />}
        {activeTab === 'runs' && (
          <ValidationRuns
            onSelectRun={handleSelectRunForEvidence}
            onNavigateReports={handleSelectRunForReport}
          />
        )}
        {activeTab === 'explorer' && <SignalExplorer />}
        {activeTab === 'tests' && <TestResults initialRunId={selectedRunId} />}
        {activeTab === 'faults' && <FaultInjection onRunCompleted={handleRunCompleted} />}
        {activeTab === 'reports' && <Reports initialRunId={selectedRunId} />}
        {activeTab === 'health' && <SystemHealth />}
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500 font-mono">
        <span>WindCtrl Validate &bull; Production-Grade Wind Turbine Controller Validation Platform &bull; IEC 61400 Benchmark</span>
      </footer>
    </div>
  );
}

export default App;

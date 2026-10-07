import React from 'react';
import { 
  Activity, 
  Layers, 
  LineChart, 
  CheckSquare, 
  Flame, 
  FileText, 
  Server, 
  Wind
} from 'lucide-react';

export type TabType = 
  | 'overview' 
  | 'runs' 
  | 'explorer' 
  | 'tests' 
  | 'faults' 
  | 'reports' 
  | 'health';

interface NavbarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  systemHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange, systemHealthy }) => {
  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: Activity },
    { id: 'runs' as TabType, label: 'Validation Runs', icon: Layers },
    { id: 'explorer' as TabType, label: 'Signal Explorer', icon: LineChart },
    { id: 'tests' as TabType, label: 'Test Results', icon: CheckSquare },
    { id: 'faults' as TabType, label: 'Fault Injection', icon: Flame },
    { id: 'reports' as TabType, label: 'Reports', icon: FileText },
    { id: 'health' as TabType, label: 'System Health', icon: Server },
  ];

  return (
    <header className="bg-industrial-navy text-white border-b border-slate-700 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-industrial-teal flex items-center justify-center text-white shadow-inner">
              <Wind size={22} className="animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white">WindCtrl</span>
                <span className="bg-sky-500/20 text-sky-300 border border-sky-400/30 text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold">
                  Validate v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-300 hidden sm:block">
                Turbine Controller Validation & Automated Reporting
              </p>
            </div>
          </div>

          {/* Center Nav Items */}
          <nav className="flex space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-industrial-teal text-white shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <Icon size={16} />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Status Badge */}
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700 text-xs font-mono">
              <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-400' : 'bg-rose-400'} animate-ping`} />
              <span className="text-slate-300 hidden lg:inline">NREL 5MW</span>
              <span className="text-emerald-400 font-semibold">{systemHealthy ? 'ONLINE' : 'OFFLINE'}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  limit?: string;
  status?: 'nominal' | 'warning' | 'critical';
  subtitle?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  limit,
  status = 'nominal',
  subtitle,
}) => {
  const statusStyles = {
    nominal: 'border-l-industrial-teal text-slate-800',
    warning: 'border-l-amber-500 text-amber-900',
    critical: 'border-l-rose-500 text-rose-900',
  };

  return (
    <div className={`bg-white border border-slate-200 border-l-4 rounded-md p-4 shadow-sm ${statusStyles[status]}`}>
      <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
        <span>{title}</span>
        {limit && <span className="text-[11px] font-mono text-slate-400">Limit: {limit}</span>}
      </div>
      <div className="flex items-baseline gap-1.5 mt-1">
        <span className="text-2xl font-bold font-mono tracking-tight">{value}</span>
        {unit && <span className="text-xs font-medium text-slate-500">{unit}</span>}
      </div>
      {subtitle && (
        <div className="mt-1 text-xs text-slate-500 truncate">
          {subtitle}
        </div>
      )}
    </div>
  );
};

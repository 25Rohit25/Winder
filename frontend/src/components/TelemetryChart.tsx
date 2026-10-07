import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { Download } from 'lucide-react';

interface TelemetryChartProps {
  title: string;
  data: any[];
  xKey?: string;
  lines: Array<{
    key: string;
    name: string;
    color: string;
    unit?: string;
    yAxisId?: string;
  }>;
  referenceLines?: Array<{
    y: number;
    label: string;
    color?: string;
    yAxisId?: string;
  }>;
  height?: number;
  yAxisUnit?: string;
  yAxisLabel?: string;
  secondaryYAxisLabel?: string;
  secondaryYAxisUnit?: string;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  title,
  data,
  xKey = 'timestamp',
  lines,
  referenceLines = [],
  height = 280,
  yAxisUnit = '',
  yAxisLabel = '',
  secondaryYAxisLabel = '',
  secondaryYAxisUnit = '',
}) => {
  const exportCsv = () => {
    if (!data.length) return;
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map((d) => Object.values(d).join(',')).join('\n');
    const blob = new Blob([`${headers}\n${rows}`], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '_')}_data.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasSecondaryAxis = lines.some((l) => l.yAxisId === 'right');

  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
        <h3 className="text-sm font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-industrial-teal" />
          {title}
        </h3>
        <button
          onClick={exportCsv}
          className="flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-industrial-teal px-2 py-1 rounded hover:bg-slate-50 border border-slate-200"
          title="Download chart data as CSV"
        >
          <Download size={13} />
          <span>Export CSV</span>
        </button>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, left: -4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey={xKey}
              stroke="#94a3b8"
              fontSize={11}
              tickFormatter={(v) => `${Number(v).toFixed(1)}s`}
            />
            <YAxis
              yAxisId="left"
              stroke="#94a3b8"
              fontSize={11}
              unit={yAxisUnit}
              label={
                yAxisLabel
                  ? { value: yAxisLabel, angle: -90, position: 'insideLeft', fontSize: 10, fill: '#64748b' }
                  : undefined
              }
            />
            {hasSecondaryAxis && (
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#94a3b8"
                fontSize={11}
                unit={secondaryYAxisUnit}
                label={
                  secondaryYAxisLabel
                    ? { value: secondaryYAxisLabel, angle: 90, position: 'insideRight', fontSize: 10, fill: '#64748b' }
                    : undefined
                }
              />
            )}
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#cbd5e1',
                borderRadius: '4px',
                fontSize: '12px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.08)',
              }}
              formatter={(value: any, name: any, item: any) => {
                const lineCfg = lines.find((l) => l.name === name || l.key === item?.dataKey);
                const unit = lineCfg?.unit || '';
                return [`${Number(value).toFixed(2)} ${unit}`, name];
              }}
              labelFormatter={(label) => `Time: ${Number(label).toFixed(2)}s`}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
              iconType="plainline"
            />
            {referenceLines.map((ref, idx) => (
              <ReferenceLine
                key={idx}
                y={ref.y}
                yAxisId={ref.yAxisId || 'left'}
                stroke={ref.color || '#ef4444'}
                strokeDasharray="4 4"
                label={{
                  value: ref.label,
                  fill: ref.color || '#ef4444',
                  fontSize: 10,
                  position: 'right',
                }}
              />
            ))}
            {lines.map((l) => (
              <Line
                key={l.key}
                type="monotone"
                dataKey={l.key}
                name={l.name}
                stroke={l.color}
                strokeWidth={1.8}
                dot={false}
                yAxisId={l.yAxisId || 'left'}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { ValidationStatus } from '../types';

interface StatusBadgeProps {
  status: ValidationStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const configs = {
    PASS: {
      bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      icon: CheckCircle2,
      label: 'PASS',
      dot: 'bg-emerald-500',
    },
    WARNING: {
      bg: 'bg-amber-50 text-amber-800 border-amber-200',
      icon: AlertTriangle,
      label: 'WARNING',
      dot: 'bg-amber-500',
    },
    FAIL: {
      bg: 'bg-rose-50 text-rose-800 border-rose-200',
      icon: XCircle,
      label: 'FAIL',
      dot: 'bg-rose-500',
    },
  };

  const c = configs[status] || configs.PASS;
  const Icon = c.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-semibold',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-bold',
  };

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 16,
  };

  return (
    <span className={`inline-flex items-center rounded-full border ${c.bg} ${sizeClasses[size]}`}>
      <Icon size={iconSizes[size]} className="shrink-0" />
      <span>{c.label}</span>
    </span>
  );
};

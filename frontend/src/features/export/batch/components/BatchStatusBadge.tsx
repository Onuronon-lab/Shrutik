import React from 'react';
import {
  ClockIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import type { ExportBatchStatus } from '../types';

interface BatchStatusBadgeProps {
  status: ExportBatchStatus;
}

const badgeConfig = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon, label: 'Pending' },
  processing: { color: 'bg-blue-100 text-blue-800', icon: ArrowPathIcon, label: 'Processing' },
  completed: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon, label: 'Completed' },
  failed: { color: 'bg-red-100 text-red-800', icon: XCircleIcon, label: 'Failed' },
} as const;

export const BatchStatusBadge: React.FC<BatchStatusBadgeProps> = ({ status }) => {
  const config = badgeConfig[status] ?? badgeConfig.pending;
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
    >
      <Icon className="h-4 w-4 mr-1" />
      {config.label}
    </span>
  );
};

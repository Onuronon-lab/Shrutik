import React from 'react';
import { FunnelIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';

interface BatchFiltersProps {
  statusFilter: string;
  onStatusChange: (value: string) => void;
  onRefresh: () => void;
  t: TFunction<'translation'>;
}

export const BatchFilters: React.FC<BatchFiltersProps> = ({
  statusFilter,
  onStatusChange,
  onRefresh,
  t,
}) => {
  return (
    <div className="bg-card rounded-lg shadow-md p-4 mb-6 border border-border">
      <div className="flex items-center space-x-4">
        <FunnelIcon className="h-5 w-5 text-secondary-foreground" />
        <select
          value={statusFilter}
          onChange={e => onStatusChange(e.target.value)}
          className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
        >
          <option value="">{t('export.filter.all_statuses')}</option>
          <option value="pending">{t('export.filter.pending')}</option>
          <option value="processing">{t('export.filter.processing')}</option>
          <option value="completed">{t('export.filter.completed')}</option>
          <option value="failed">{t('export.filter.failed')}</option>
        </select>
        <button
          onClick={onRefresh}
          className="px-4 py-2 border border-border rounded-lg hover:bg-accent flex items-center space-x-2"
        >
          <ArrowPathIcon className="h-4 w-4" />
          <span>{t('export.filter.refresh')}</span>
        </button>
      </div>
    </div>
  );
};

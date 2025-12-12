import React from 'react';
import { ClockIcon, DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../../../components/common/LoadingSpinner';
import type { TFunction } from 'i18next';
import { ExportHistoryResponse } from '../../../types/export';
import { ExportHistoryFilters } from '../types';

interface ExportHistoryPanelProps {
  history: ExportHistoryResponse | null;
  loading: boolean;
  error: string | null;
  filters: ExportHistoryFilters;
  onFiltersChange: (updates: Partial<ExportHistoryFilters>) => void;
  page: number;
  onPageChange: (page: number) => void;
  formatDate: (value: string) => string;
  formatFileSize: (value?: number) => string;
  t: TFunction<'translation'>;
}

export const ExportHistoryPanel: React.FC<ExportHistoryPanelProps> = ({
  history,
  loading,
  error,
  filters,
  onFiltersChange,
  page,
  onPageChange,
  formatDate,
  formatFileSize,
  t,
}) => {
  const handleFilterChange = (field: keyof ExportHistoryFilters, value: string) => {
    onFiltersChange({ [field]: value });
  };

  const totalCount = history?.total_count ?? 0;
  const pageSize = history?.page_size ?? 20;
  const hasPagination = totalCount > pageSize;

  return (
    <div className="bg-card rounded-lg shadow-md border border-border">
      <div className="p-6 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground flex items-center">
          <ClockIcon className="h-6 w-6 text-info mr-2" />
          {t('exportPage-export-history')}
        </h3>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-secondary-foreground mb-1">
              {t('exportPage-export-type')}
            </label>
            <select
              value={filters.export_type}
              onChange={e => handleFilterChange('export_type', e.target.value)}
              className="w-full px-3 py-3 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
            >
              <option value="">{t('exportPage-all-types')}</option>
              <option value="dataset">{t('exportPage-dataset')}</option>
              <option value="metadata">{t('exportPage-metadata')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary-foreground mb-1">
              {t('exportPage-from-date')}
            </label>
            <input
              type="date"
              value={filters.date_from}
              onChange={e => handleFilterChange('date_from', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary-foreground mb-1">
              {t('exportPage-to-date')}
            </label>
            <input
              type="date"
              value={filters.date_to}
              onChange={e => handleFilterChange('date_to', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
            />
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-12 text-destructive">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            {error}
          </div>
        ) : history?.logs.length ? (
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-background">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-export-id')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-type')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-format')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-records')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-size')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-user')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t('exportPage-date')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {history.logs.map(log => (
                <tr key={log.id} className="hover:bg-background">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {log.export_id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        log.export_type === 'dataset'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-success text-primary-foreground'
                      }`}
                    >
                      {log.export_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground uppercase">
                    {log.format}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {log.records_exported.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {formatFileSize(log.file_size_bytes)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {log.user_email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {formatDate(log.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-accent" />
            <h3 className="mt-2 text-sm font-medium text-foreground">
              {t('exportPage-no-export-history-title')}
            </h3>
            <p className="mt-1 text-sm text-secondary-foreground">
              {t('exportPage-no-export-history-desc')}
            </p>
          </div>
        )}
      </div>

      {hasPagination && (
        <div className="px-6 py-3 border-t border-border flex items-center justify-between">
          <div className="text-sm text-secondary-foreground">
            {t('exportPage-showing-results', {
              start: (page - 1) * pageSize + 1,
              end: Math.min(page * pageSize, totalCount),
              total: totalCount,
            })}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1 border border-border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-background"
            >
              {t('exportPage-previous')}
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page * pageSize >= totalCount}
              className="px-3 py-1 border border-border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-background"
            >
              {t('exportPage-next')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

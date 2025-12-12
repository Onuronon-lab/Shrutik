import React from 'react';
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import type { ExportBatch } from '../types';
import LoadingSpinner from '../../../../components/common/LoadingSpinner';
import { Button } from '../../../../components/ui';
import { BatchStatusBadge } from './BatchStatusBadge';
import { formatDate, formatFileSize } from '../utils';

interface BatchTableProps {
  batches: ExportBatch[];
  loading: boolean;
  totalCount: number;
  page: number;
  onPageChange: (page: number) => void;
  onDownload: (batchId: string) => void;
  onRetry?: (batchId: string) => void;
  canRetryFailed: boolean;
  quotaExhausted: boolean;
  onEmptyAction?: () => void;
  t: TFunction<'translation'>;
}

export const BatchTable: React.FC<BatchTableProps> = ({
  batches,
  loading,
  totalCount,
  page,
  onPageChange,
  onDownload,
  onRetry,
  canRetryFailed,
  quotaExhausted,
  onEmptyAction,
  t,
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (batches.length === 0) {
    return (
      <div className="text-center py-12 bg-card rounded-lg shadow-md border border-border">
        <InformationCircleIcon className="mx-auto h-12 w-12 text-secondary-foreground mb-4" />
        <p className="text-secondary-foreground">{t('export.empty.title')}</p>
        {onEmptyAction && (
          <Button variant="outline" className="mt-4" onClick={onEmptyAction}>
            {t('export.empty.create_first')}
          </Button>
        )}
      </div>
    );
  }

  const pageSize = 10;
  const showPagination = totalCount > pageSize;

  return (
    <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-accent">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                {t('export.table.batch_id')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                {t('export.table.status')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                {t('export.table.chunks')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                {t('export.table.size')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                {t('export.table.created')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                {t('export.table.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-card divide-y divide-border">
            {batches.map(batch => (
              <tr key={batch.batch_id} className="hover:bg-accent">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-foreground">
                  {batch.batch_id.substring(0, 8)}...
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <BatchStatusBadge status={batch.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {batch.chunk_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {formatFileSize(batch.file_size_bytes)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-foreground">
                  {formatDate(batch.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {batch.status === 'completed' && (
                    <button
                      onClick={() => onDownload(batch.batch_id)}
                      disabled={quotaExhausted}
                      className="text-primary hover:text-primary-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
                    >
                      <ArrowDownTrayIcon className="h-4 w-4" />
                      <span>{t('export.action.download')}</span>
                    </button>
                  )}
                  {batch.status === 'failed' && canRetryFailed && onRetry && (
                    <button
                      onClick={() => onRetry(batch.batch_id)}
                      className="text-yellow-600 hover:text-yellow-700 flex items-center space-x-1"
                    >
                      <ArrowPathIcon className="h-4 w-4" />
                      <span>{t('export.action.retry')}</span>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showPagination && (
        <div className="bg-accent px-6 py-4 flex items-center justify-between border-t border-border">
          <div className="text-sm text-secondary-foreground">
            {t('export.pagination.showing', {
              start: (page - 1) * pageSize + 1,
              end: Math.min(page * pageSize, totalCount),
              total: totalCount,
            })}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1 border border-border rounded hover:bg-card disabled:opacity-50"
            >
              {t('export.pagination.previous')}
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page * pageSize >= totalCount}
              className="px-3 py-1 border border-border rounded hover:bg-card disabled:opacity-50"
            >
              {t('export.pagination.next')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

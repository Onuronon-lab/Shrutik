import React from 'react';
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
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
  userRole?: string | undefined;
  onEmptyAction?: () => void;
  t: TFunction<'translation'>;
}

// Progress indicator component for processing batches
const ProcessingProgress: React.FC<{ batch: ExportBatch; t: TFunction<'translation'> }> = ({
  batch,
  t,
}) => {
  // Estimate progress based on time elapsed (this is a rough estimate)
  const createdAt = new Date(batch.created_at);
  const now = new Date();
  const elapsedMinutes = Math.floor((now.getTime() - createdAt.getTime()) / (1000 * 60));

  // Rough estimate: small batches take ~5 minutes, large batches take ~15 minutes
  const estimatedTotalMinutes = Math.max(5, Math.min(15, batch.chunk_count / 10));
  const progress = Math.min(95, (elapsedMinutes / estimatedTotalMinutes) * 100);
  const remainingMinutes = Math.max(0, estimatedTotalMinutes - elapsedMinutes);

  return (
    <div className="space-y-1">
      <div className="flex items-center text-xs text-secondary-foreground">
        <div className="w-16 bg-gray-200 rounded-full h-1.5 mr-2">
          <div
            className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span>{Math.round(progress)}%</span>
      </div>
      {remainingMinutes > 0 && (
        <div className="flex items-center text-xs text-secondary-foreground">
          <ClockIcon className="h-3 w-3 mr-1" />
          <span>{t('export.table.estimated_time', { minutes: remainingMinutes })}</span>
        </div>
      )}
    </div>
  );
};

// Download availability indicator with enhanced state management
const DownloadAvailability: React.FC<{
  batch: ExportBatch;
  quotaExhausted: boolean;
  userRole?: string | undefined;
  onDownload: (batchId: string) => void;
  t: TFunction<'translation'>;
}> = ({ batch, quotaExhausted, userRole, onDownload, t }) => {
  const isCompleted = batch.status === 'completed';
  const isAdmin = userRole === 'admin';
  const canDownload = isCompleted && (!quotaExhausted || isAdmin);

  // Get tooltip message based on state
  const getTooltipMessage = () => {
    if (!isCompleted) {
      return batch.status === 'processing'
        ? t('export.tooltip.processing')
        : batch.status === 'pending'
          ? t('export.tooltip.pending')
          : batch.status === 'failed'
            ? t('export.tooltip.failed')
            : t('export.tooltip.not_ready');
    }

    if (quotaExhausted && !isAdmin) {
      return t('export.tooltip.quota_exhausted');
    }

    return t('export.tooltip.ready_to_download');
  };

  const tooltipMessage = getTooltipMessage();

  if (!isCompleted) {
    return (
      <div
        className="flex items-center text-xs text-secondary-foreground cursor-help"
        title={tooltipMessage}
      >
        <ClockIcon className="h-3 w-3 mr-1" />
        <span>{t('export.table.not_ready')}</span>
      </div>
    );
  }

  if (quotaExhausted && !isAdmin) {
    return (
      <div
        className="flex items-center text-xs text-destructive cursor-help"
        title={tooltipMessage}
      >
        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
        <span>{t('export.table.quota_exhausted')}</span>
      </div>
    );
  }

  return (
    <button
      onClick={() => onDownload(batch.batch_id)}
      disabled={!canDownload}
      className={`flex items-center text-sm font-medium transition-colors ${
        canDownload
          ? 'text-primary hover:text-primary-hover cursor-pointer'
          : 'text-secondary-foreground cursor-not-allowed opacity-50'
      }`}
      title={tooltipMessage}
    >
      <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
      <span>{t('export.action.download')}</span>
    </button>
  );
};

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
  userRole,
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
                {t('export.table.progress')}
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
                {t('export.table.download')}
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
                  <div className="flex items-center">
                    <span>{batch.batch_id.substring(0, 8)}...</span>
                    {batch.status === 'completed' && (
                      <CheckCircleIcon
                        className="h-4 w-4 text-success ml-2"
                        title={t('export.table.ready_to_download')}
                      />
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <BatchStatusBadge status={batch.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {batch.status === 'processing' ? (
                    <ProcessingProgress batch={batch} t={t} />
                  ) : batch.status === 'pending' ? (
                    <div className="flex items-center text-xs text-secondary-foreground">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      <span>{t('export.table.queued')}</span>
                    </div>
                  ) : batch.status === 'completed' ? (
                    <div className="flex items-center text-xs text-success">
                      <CheckCircleIcon className="h-3 w-3 mr-1" />
                      <span>{t('export.table.ready')}</span>
                    </div>
                  ) : batch.status === 'failed' ? (
                    <div className="flex items-center text-xs text-destructive">
                      <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                      <span>{t('export.table.failed')}</span>
                    </div>
                  ) : null}
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
                <td className="px-6 py-4 whitespace-nowrap">
                  <DownloadAvailability
                    batch={batch}
                    quotaExhausted={quotaExhausted}
                    userRole={userRole}
                    onDownload={onDownload}
                    t={t}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
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

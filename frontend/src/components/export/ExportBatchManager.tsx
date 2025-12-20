import React, { useState, memo } from 'react';
import { useTranslation } from 'react-i18next';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { exportService } from '../../services/export.service';
import { useModal } from '../../hooks/useModal';
import { useErrorHandler } from '../../hooks/useErrorHandler';
import {
  BatchHeader,
  BatchQuotaCard,
  BatchFilters,
  BatchFeedback,
  BatchTable,
  BatchCreateModal,
  BatchSuccessModal,
} from '../../features/export/batch/components';
import { useBatchData } from '../../features/export/batch/hooks/useBatchData';
import { useDownloadQuota } from '../../features/export/batch/hooks/useDownloadQuota';
import type { CreateBatchFormValues, ExportBatch } from '../../features/export/batch/types';

const DEFAULT_CREATE_FILTERS: CreateBatchFormValues = {
  date_from: '',
  date_to: '',
  min_duration: '',
  max_duration: '',
  force_create: true,
};

const ExportBatchManager: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [success, setSuccess] = useState<string | null>(null);
  const createModal = useModal();
  const successModal = useModal();
  const { error, setError, handleError } = useErrorHandler();
  const [createFilters, setCreateFilters] = useState<CreateBatchFormValues>(DEFAULT_CREATE_FILTERS);
  const [createLoading, setCreateLoading] = useState(false);
  const [createdBatch, setCreatedBatch] = useState<ExportBatch | null>(null);

  const hasAccess = user?.role === 'sworik_developer' || user?.role === 'admin';

  const {
    batches,
    totalCount,
    page,
    setPage,
    statusFilter,
    setStatusFilter,
    loading,
    refresh: refreshBatches,
  } = useBatchData({
    enabled: hasAccess,
    onError: setError,
    defaultErrorMessage: t('export.error.load_batches'),
  });

  const { quota, refresh: refreshQuota } = useDownloadQuota({ enabled: hasAccess });

  const updateCreateFilters = (partial: Partial<CreateBatchFormValues>) => {
    setCreateFilters(prev => ({ ...prev, ...partial }));
  };

  const handleCreateBatch = async () => {
    try {
      setCreateLoading(true);
      setError(null);
      setSuccess(null);

      const filters: any = {
        force_create: createFilters.force_create,
      };

      if (createFilters.date_from) filters.date_from = createFilters.date_from;
      if (createFilters.date_to) filters.date_to = createFilters.date_to;
      if (createFilters.min_duration) filters.min_duration = parseFloat(createFilters.min_duration);
      if (createFilters.max_duration) filters.max_duration = parseFloat(createFilters.max_duration);

      const response = await exportService.createExportBatch(filters);

      // Store the created batch and show success modal
      setCreatedBatch({
        id: response.id || 0,
        batch_id: response.batch_id,
        archive_path: response.archive_path || '',
        status: response.status || 'pending',
        storage_type: response.storage_type || 'local',
        chunk_count: response.chunk_count,
        file_size_bytes: response.file_size_bytes,
        chunk_ids: response.chunk_ids || [],
        exported: response.exported || false,
        error_message: response.error_message,
        retry_count: response.retry_count || 0,
        checksum: response.checksum,
        compression_level: response.compression_level,
        format_version: response.format_version || '1.0',
        recording_id_range: response.recording_id_range,
        language_stats: response.language_stats,
        total_duration_seconds: response.total_duration_seconds,
        filter_criteria: response.filter_criteria || filters,
        created_at: response.created_at || new Date().toISOString(),
        completed_at: response.completed_at,
        created_by_id: response.created_by_id,
      });

      createModal.close();
      successModal.open();

      setCreateFilters({
        date_from: '',
        date_to: '',
        min_duration: '',
        max_duration: '',
        force_create: true,
      });

      refreshBatches();
    } catch (err: any) {
      handleError(err);
      console.error('Create batch error:', err);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDownload = async (batchId: string) => {
    try {
      // Check quota first (skip for unlimited users)
      if (quota && quota.downloads_remaining <= 0 && !quota.is_unlimited) {
        const resetTime = quota.reset_time ? new Date(quota.reset_time) : null;
        const hoursUntilReset = resetTime
          ? Math.ceil((resetTime.getTime() - new Date().getTime()) / (1000 * 60 * 60))
          : 0;

        setError({
          error: t('export.error.quota_exceeded_title'),
          details: {
            downloads_today: quota.downloads_today,
            daily_limit: quota.daily_limit,
            reset_time: quota.reset_time,
            hours_until_reset: hoursUntilReset,
            suggestions: [
              resetTime
                ? t('export.error.quota_suggestion_wait', { resetTime: resetTime.toLocaleString() })
                : 'Contact admin for assistance',
              t('export.error.quota_suggestion_admin'),
            ],
          },
        });
        return;
      }

      const response = await exportService.downloadExportBatch(batchId);

      // If R2 storage, response contains download_url
      if (response.download_url) {
        window.open(response.download_url, '_blank');
      } else {
        // For local storage, the response is the file blob
        const blob = new Blob([response], { type: 'application/x-tar' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `export_batch_${batchId}.tar.zst`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }

      refreshQuota();
      setSuccess(t('export.success.download_started'));
    } catch (err: any) {
      handleError(err);
      console.error('Download error:', err);
    }
  };

  const handleCreateAnother = () => {
    createModal.open();
  };

  // Check if user has export permissions
  if (user?.role !== 'sworik_developer' && user?.role !== 'admin') {
    return (
      <div className="bg-destructive border border-destructive-border rounded-lg p-6">
        <div className="flex items-center">
          <ExclamationTriangleIcon className="h-6 w-6 text-destructive-foreground mr-3" />
          <div>
            <h3 className="text-lg font-medium text-destructive-foreground">
              {t('export.access_denied.title')}
            </h3>
            <p className="text-destructive-foreground mt-1">{t('export.access_denied.message')}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <BatchHeader t={t} onCreateClick={createModal.open} />
      <BatchQuotaCard quota={quota} userRole={user?.role} t={t} />
      <BatchFeedback error={error || null} success={success} />
      <BatchFilters
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        onRefresh={refreshBatches}
        t={t}
      />
      <BatchTable
        batches={batches}
        loading={loading}
        totalCount={totalCount}
        page={page}
        onPageChange={setPage}
        onDownload={handleDownload}
        canRetryFailed={user?.role === 'admin'}
        quotaExhausted={quota ? quota.downloads_remaining <= 0 && !quota.is_unlimited : false}
        userRole={user?.role}
        onEmptyAction={createModal.open}
        t={t}
      />
      <BatchCreateModal
        isOpen={createModal.isOpen}
        onClose={createModal.close}
        values={createFilters}
        onChange={updateCreateFilters}
        onSubmit={handleCreateBatch}
        loading={createLoading}
        t={t}
      />
      <BatchSuccessModal
        isOpen={successModal.isOpen}
        onClose={successModal.close}
        batch={createdBatch}
        onDownload={handleDownload}
        onCreateAnother={handleCreateAnother}
        canDownload={
          createdBatch?.status === 'completed' &&
          (!quota || quota.downloads_remaining > 0 || quota.is_unlimited)
        }
        downloadDisabledReason={
          quota && quota.downloads_remaining <= 0 && !quota.is_unlimited
            ? t('export.error.quota_exceeded', {
                limit: quota.daily_limit,
                resetTime: quota.reset_time ? new Date(quota.reset_time).toLocaleString() : 'N/A',
              })
            : createdBatch?.status !== 'completed'
              ? t('export.success.modal.batch_not_ready')
              : undefined
        }
        t={t}
      />
    </div>
  );
};

export default memo(ExportBatchManager);
export { ExportBatchManager };

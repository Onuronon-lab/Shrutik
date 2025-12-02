import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowDownTrayIcon,
  PlusIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  FunnelIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import { useTranslation } from 'react-i18next';

interface ExportBatch {
  batch_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  storage_type: 'local' | 'r2';
  chunk_count: number;
  file_size_bytes?: number;
  created_at: string;
  completed_at?: string;
  filter_criteria?: any;
}

interface DownloadQuota {
  downloads_today: number;
  downloads_remaining: number;
  daily_limit: number;
  reset_time: string;
}

const ExportBatchManager: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();

  const [batches, setBatches] = useState<ExportBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [quota, setQuota] = useState<DownloadQuota | null>(null);

  // Create batch state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createFilters, setCreateFilters] = useState({
    date_from: '',
    date_to: '',
    min_duration: '',
    max_duration: '',
    force_create: true,
  });

  // List filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalBatches, setTotalBatches] = useState(0);

  const loadBatches = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: page,
        page_size: 10,
      };

      if (statusFilter) {
        params.status_filter = statusFilter;
      }

      const response = await apiService.listExportBatches(params);
      setBatches(response.batches || []);
      setTotalBatches(response.total_count || 0);
      // Clear any previous errors on successful load
      setError(null);
    } catch (err: any) {
      // Only show error for actual API failures, not empty results
      console.error('Load batches error:', err);

      // Check if it's a 404 or the endpoint doesn't exist
      if (err.response?.status === 404) {
        // Endpoint not found - treat as empty list
        setBatches([]);
        setTotalBatches(0);
        setError(null);
      } else if (err.response?.status === 500) {
        // Server error - likely database not migrated
        setError('Server error. Please ensure database migrations are run: alembic upgrade head');
        setBatches([]);
        setTotalBatches(0);
      } else {
        // Real error - show error message
        const errorMessage = err.response?.data?.detail || t('export.error.load_batches');
        setError(errorMessage);
        setBatches([]);
        setTotalBatches(0);
      }
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, t]);

  const loadQuota = async () => {
    try {
      const quotaData = await apiService.getDownloadQuota();
      setQuota(quotaData);
    } catch (err) {
      console.error('Failed to load quota:', err);
    }
  };

  useEffect(() => {
    if (user?.role === 'sworik_developer' || user?.role === 'admin') {
      loadBatches();
      loadQuota();
    }
  }, [user, loadBatches]);

  const handleCreateBatch = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const filters: any = {
        force_create: createFilters.force_create,
      };

      if (createFilters.date_from) filters.date_from = createFilters.date_from;
      if (createFilters.date_to) filters.date_to = createFilters.date_to;
      if (createFilters.min_duration) filters.min_duration = parseFloat(createFilters.min_duration);
      if (createFilters.max_duration) filters.max_duration = parseFloat(createFilters.max_duration);

      const response = await apiService.createExportBatch(filters);

      setSuccess(t('export.success.batch_created', { count: response.chunk_count }));
      setShowCreateModal(false);
      setCreateFilters({
        date_from: '',
        date_to: '',
        min_duration: '',
        max_duration: '',
        force_create: true,
      });

      // Reload batches
      loadBatches();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create export batch');
      console.error('Create batch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (batchId: string) => {
    try {
      setError(null);

      // Check quota first
      if (quota && quota.downloads_remaining <= 0) {
        setError(
          t('export.error.quota_exceeded', {
            limit: quota.daily_limit,
            resetTime: new Date(quota.reset_time).toLocaleString(),
          })
        );
        return;
      }

      const response = await apiService.downloadExportBatch(batchId);

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

      // Reload quota
      loadQuota();
      setSuccess(t('export.success.download_started'));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to download export batch');
      console.error('Download error:', err);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon, text: 'Pending' },
      processing: { color: 'bg-blue-100 text-blue-800', icon: ArrowPathIcon, text: 'Processing' },
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon, text: 'Completed' },
      failed: { color: 'bg-red-100 text-red-800', icon: XCircleIcon, text: 'Failed' },
    };

    const badge = badges[status as keyof typeof badges] || badges.pending;
    const Icon = badge.icon;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}
      >
        <Icon className="h-4 w-4 mr-1" />
        {badge.text}
      </span>
    );
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
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
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">{t('export.title')}</h1>
            <p className="text-secondary-foreground">{t('export.subtitle')}</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary-hover flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>{t('export.create_batch')}</span>
          </button>
        </div>
      </div>

      {/* Download Quota Card */}
      {quota && (
        <div className="bg-card rounded-lg shadow-md p-6 mb-6 border border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ArrowDownTrayIcon className="h-8 w-8 text-primary mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-foreground">{t('export.quota.title')}</h3>
                <p className="text-sm text-secondary-foreground">
                  {t('export.quota.remaining', {
                    remaining: quota.downloads_remaining,
                    limit: quota.daily_limit,
                  })}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-foreground">
                {quota.downloads_today}/{quota.daily_limit}
              </div>
              <p className="text-xs text-secondary-foreground">
                Resets at {new Date(quota.reset_time).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${(quota.downloads_today / quota.daily_limit) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Error/Success Messages */}
      {error && !loading && (
        <div className="bg-destructive border border-destructive-border rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-destructive-foreground mr-2" />
            <p className="text-destructive-foreground">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-success border border-success-border rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-success-foreground mr-2" />
            <p className="text-success-foreground">{success}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-card rounded-lg shadow-md p-4 mb-6 border border-border">
        <div className="flex items-center space-x-4">
          <FunnelIcon className="h-5 w-5 text-secondary-foreground" />
          <select
            value={statusFilter}
            onChange={e => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
          >
            <option value="">{t('export.filter.all_statuses')}</option>
            <option value="pending">{t('export.filter.pending')}</option>
            <option value="processing">{t('export.filter.processing')}</option>
            <option value="completed">{t('export.filter.completed')}</option>
            <option value="failed">{t('export.filter.failed')}</option>
          </select>
          <button
            onClick={loadBatches}
            className="px-4 py-2 border border-border rounded-lg hover:bg-accent flex items-center space-x-2"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>{t('export.filter.refresh')}</span>
          </button>
        </div>
      </div>

      {/* Batches List */}
      <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <LoadingSpinner />
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-12">
            <InformationCircleIcon className="mx-auto h-12 w-12 text-secondary-foreground mb-4" />
            <p className="text-secondary-foreground">{t('export.empty.title')}</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-primary hover:underline"
            >
              {t('export.empty.create_first')}
            </button>
          </div>
        ) : (
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
                    <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(batch.status)}</td>
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
                          onClick={() => handleDownload(batch.batch_id)}
                          disabled={quota?.downloads_remaining === 0}
                          className="text-primary hover:text-primary-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                          <span>{t('export.action.download')}</span>
                        </button>
                      )}
                      {batch.status === 'failed' && user?.role === 'admin' && (
                        <button
                          onClick={() => {
                            /* TODO: Implement retry */
                          }}
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
        )}

        {/* Pagination */}
        {totalBatches > 10 && (
          <div className="bg-accent px-6 py-4 flex items-center justify-between border-t border-border">
            <div className="text-sm text-secondary-foreground">
              {t('export.pagination.showing', {
                start: (page - 1) * 10 + 1,
                end: Math.min(page * 10, totalBatches),
                total: totalBatches,
              })}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-border rounded hover:bg-card disabled:opacity-50"
              >
                {t('export.pagination.previous')}
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 10 >= totalBatches}
                className="px-3 py-1 border border-border rounded hover:bg-card disabled:opacity-50"
              >
                {t('export.pagination.next')}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Batch Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg shadow-xl p-6 max-w-md w-full mx-4 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              {t('export.modal.title')}
            </h3>

            <div className="space-y-4">
              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-secondary-foreground mb-2">
                  {t('export.modal.date_range')}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="date"
                    value={createFilters.date_from}
                    onChange={e =>
                      setCreateFilters(prev => ({ ...prev, date_from: e.target.value }))
                    }
                    className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
                    placeholder={t('export.modal.date_from')}
                  />
                  <input
                    type="date"
                    value={createFilters.date_to}
                    onChange={e => setCreateFilters(prev => ({ ...prev, date_to: e.target.value }))}
                    className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
                    placeholder={t('export.modal.date_to')}
                  />
                </div>
              </div>

              {/* Duration Range */}
              <div>
                <label className="block text-sm font-medium text-secondary-foreground mb-2">
                  {t('export.modal.duration_range')}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    step="0.1"
                    value={createFilters.min_duration}
                    onChange={e =>
                      setCreateFilters(prev => ({ ...prev, min_duration: e.target.value }))
                    }
                    className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
                    placeholder={t('export.modal.duration_min')}
                  />
                  <input
                    type="number"
                    step="0.1"
                    value={createFilters.max_duration}
                    onChange={e =>
                      setCreateFilters(prev => ({ ...prev, max_duration: e.target.value }))
                    }
                    className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
                    placeholder={t('export.modal.duration_max')}
                  />
                </div>
              </div>

              {/* Force Create */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="force_create"
                  checked={createFilters.force_create}
                  onChange={e =>
                    setCreateFilters(prev => ({ ...prev, force_create: e.target.checked }))
                  }
                  className="h-4 w-4 text-primary focus:ring-ring border-border rounded"
                />
                <label htmlFor="force_create" className="ml-2 text-sm text-secondary-foreground">
                  {t('export.modal.force_create')}
                </label>
              </div>

              {/* Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex">
                  <InformationCircleIcon className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0" />
                  <p className="text-xs text-blue-800">{t('export.modal.info')}</p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-accent"
              >
                {t('export.modal.cancel')}
              </button>
              <button
                onClick={handleCreateBatch}
                disabled={loading}
                className="flex-1 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary-hover disabled:opacity-50"
              >
                {loading ? <LoadingSpinner /> : t('export.modal.create')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExportBatchManager;

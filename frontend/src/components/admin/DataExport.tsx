import React, { useMemo, useState } from 'react';
import {
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../../contexts/AuthContext';
import {
  DatasetExportRequest,
  DatasetExportResponse,
  MetadataExportRequest,
  MetadataExportResponse,
} from '../../types/export';
import { exportService } from '../../services/export.service';
import { DatasetExportForm } from '../../features/export/components/DatasetExportForm';
import { MetadataExportPanel } from '../../features/export/components/MetadataExportPanel';
import { PlatformStatsOverview } from '../../features/export/components/PlatformStatsOverview';
import { ExportHistoryPanel } from '../../features/export/components/ExportHistoryPanel';
import { useExportStats } from '../../features/export/hooks/useExportStats';
import { useExportHistory } from '../../features/export/hooks/useExportHistory';
import { ExportTab } from '../../features/export/types';

const INITIAL_DATASET_REQUEST: DatasetExportRequest = {
  format: 'json',
  quality_filters: {
    consensus_only: false,
    validated_only: false,
  },
  include_metadata: true,
  include_audio_paths: true,
};

const INITIAL_METADATA_REQUEST: MetadataExportRequest = {
  format: 'json',
  include_statistics: true,
  include_user_stats: false,
  include_quality_metrics: true,
};

const DataExport: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();

  const [activeTab, setActiveTab] = useState<ExportTab>('dataset');
  const [datasetRequest, setDatasetRequest] =
    useState<DatasetExportRequest>(INITIAL_DATASET_REQUEST);
  const [metadataRequest, setMetadataRequest] =
    useState<MetadataExportRequest>(INITIAL_METADATA_REQUEST);
  const [datasetLoading, setDatasetLoading] = useState(false);
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'error' | 'success'; message: string } | null>(
    null
  );
  const [historyRefreshToken, setHistoryRefreshToken] = useState(0);

  const hasExportAccess = user?.role === 'sworik_developer' || user?.role === 'admin';

  const { stats } = useExportStats(hasExportAccess);
  const {
    history,
    loading: historyLoading,
    error: historyError,
    filters: historyFilters,
    setFilters: setHistoryFilters,
    page: historyPage,
    setPage: setHistoryPage,
  } = useExportHistory({
    isActive: activeTab === 'history',
    refreshToken: historyRefreshToken,
  });

  const tabs = useMemo(
    () => [
      { id: 'dataset' as ExportTab, name: t('exportTab-dataset'), icon: DocumentArrowDownIcon },
      { id: 'metadata' as ExportTab, name: t('exportTab-metadata'), icon: ClockIcon },
      { id: 'history' as ExportTab, name: t('exportTab-history'), icon: ClockIcon },
    ],
    [t]
  );

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round((bytes / Math.pow(1024, i)) * 100) / 100} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => new Date(dateString).toLocaleString();

  const getMimeType = (format: string) => {
    switch (format) {
      case 'csv':
        return 'text/csv';
      case 'jsonl':
        return 'application/jsonl';
      case 'parquet':
        return 'application/octet-stream';
      default:
        return 'application/json';
    }
  };

  const triggerDownload = (data: BlobPart, filename: string, format: string) => {
    const blob = new Blob([data], { type: getMimeType(format) });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const refreshHistoryLater = () => {
    setHistoryRefreshToken(token => token + 1);
  };

  const handleDatasetExport = async () => {
    try {
      setDatasetLoading(true);
      setFeedback(null);
      const response: DatasetExportResponse = await exportService.exportDataset(datasetRequest);
      triggerDownload(
        JSON.stringify(response.data, null, 2),
        `dataset_export_${response.export_id}.${datasetRequest.format}`,
        datasetRequest.format
      );
      setFeedback({
        type: 'success',
        message: t('dataset_export_success', { count: response.total_records }),
      });
      refreshHistoryLater();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || t('dataset_export_failed'),
      });
    } finally {
      setDatasetLoading(false);
    }
  };

  const handleMetadataExport = async () => {
    try {
      setMetadataLoading(true);
      setFeedback(null);
      const response: MetadataExportResponse = await exportService.exportMetadata(metadataRequest);
      const exportData = {
        statistics: response.statistics,
        platform_metrics: response.platform_metrics,
        ...(response.user_statistics && { user_statistics: response.user_statistics }),
        ...(response.quality_metrics && { quality_metrics: response.quality_metrics }),
      };
      triggerDownload(
        JSON.stringify(exportData, null, 2),
        `metadata_export_${response.export_id}.${metadataRequest.format}`,
        metadataRequest.format
      );
      setFeedback({
        type: 'success',
        message: t('metadata_export_success'),
      });
      refreshHistoryLater();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || t('metadata_export_failed'),
      });
    } finally {
      setMetadataLoading(false);
    }
  };

  if (!hasExportAccess) {
    return (
      <div className="bg-destructive border border-destructive-border rounded-lg p-6">
        <div className="flex items-center">
          <ExclamationTriangleIcon className="h-6 w-6 text-destructive-foreground mr-3" />
          <div>
            <h3 className="text-lg font-medium text-destructive-foreground">
              {t('access_denied')}
            </h3>
            <p className="text-destructive-foreground mt-1">{t('export_restricted')}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <ArrowDownTrayIcon className="mx-auto h-16 w-16 text-primary mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-2">{t('dataExport-title')}</h1>
        <p className="text-secondary-foreground">{t('dataExport-subtitle')}</p>
      </div>

      <PlatformStatsOverview stats={stats} t={t} />

      <div className="border-b border-border mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-primary-border text-primary'
                    : 'border-transparent text-secondary-foreground hover:text-primary hover:border-primary-border'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {feedback && (
        <div
          className={`border rounded-lg p-4 mb-6 ${
            feedback.type === 'error'
              ? 'bg-destructive border-destructive-border text-destructive-foreground'
              : 'bg-success border-success-border text-success-foreground'
          }`}
        >
          <div className="flex items-center">
            {feedback.type === 'error' ? (
              <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            ) : (
              <CheckCircleIcon className="h-5 w-5 mr-2" />
            )}
            <p>{feedback.message}</p>
          </div>
        </div>
      )}

      <div className="min-h-96">
        {activeTab === 'dataset' && (
          <DatasetExportForm
            request={datasetRequest}
            onRequestChange={setDatasetRequest}
            onExport={handleDatasetExport}
            loading={datasetLoading}
            t={t}
          />
        )}

        {activeTab === 'metadata' && (
          <MetadataExportPanel
            request={metadataRequest}
            onRequestChange={setMetadataRequest}
            onExport={handleMetadataExport}
            loading={metadataLoading}
            t={t}
          />
        )}

        {activeTab === 'history' && (
          <ExportHistoryPanel
            history={history}
            loading={historyLoading}
            error={historyError}
            filters={historyFilters}
            onFiltersChange={updates => setHistoryFilters(prev => ({ ...prev, ...updates }))}
            page={historyPage}
            onPageChange={setHistoryPage}
            formatDate={formatDate}
            formatFileSize={formatFileSize}
            t={t}
          />
        )}

        {activeTab === 'dataset' && (
          <div className="flex justify-end mt-4">
            <button
              onClick={() => {
                setDatasetRequest(INITIAL_DATASET_REQUEST);
                setFeedback(null);
              }}
              className="text-sm text-secondary-foreground hover:text-primary transition-colors"
            >
              {t('reset_form')}
            </button>
          </div>
        )}

        {activeTab === 'metadata' && (
          <div className="flex justify-end mt-4">
            <button
              onClick={() => {
                setMetadataRequest(INITIAL_METADATA_REQUEST);
                setFeedback(null);
              }}
              className="text-sm text-secondary-foreground hover:text-primary transition-colors"
            >
              {t('reset_form')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataExport;

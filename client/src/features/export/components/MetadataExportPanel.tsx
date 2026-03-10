import React from 'react';
import { ArrowDownTrayIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import { MetadataExportRequest } from '../../../types/export';
import LoadingSpinner from '../../../components/common/LoadingSpinner';

interface MetadataExportPanelProps {
  request: MetadataExportRequest;
  onRequestChange: (updater: (prev: MetadataExportRequest) => MetadataExportRequest) => void;
  onExport: () => void;
  loading: boolean;
  t: TFunction<'translation'>;
}

export const MetadataExportPanel: React.FC<MetadataExportPanelProps> = ({
  request,
  onRequestChange,
  onExport,
  loading,
  t,
}) => {
  const updateRequest = (partial: Partial<MetadataExportRequest>) => {
    onRequestChange(prev => ({ ...prev, ...partial }));
  };

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
        <ChartBarIcon className="h-6 w-6 text-success mr-2" />
        {t('exportPage-export-metadata')}
      </h3>

      <div className="max-w-md mx-auto space-y-6">
        <div>
          <label className="block text-sm font-medium text-secondary-foreground mb-2">
            {t('dataExport-format')}
          </label>
          <select
            value={request.format}
            onChange={e =>
              updateRequest({ format: e.target.value as MetadataExportRequest['format'] })
            }
            className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
          >
            <option value="json">{t('exportPage-json-format')}</option>
            <option value="csv">{t('exportPage-csv-format')}</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-secondary-foreground mb-3">
            {t('dataExport-includeOptions')}
          </label>
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="include_statistics"
                checked={request.include_statistics}
                onChange={e => updateRequest({ include_statistics: e.target.checked })}
                className="h-5 w-5 border-border rounded"
              />
              <label
                htmlFor="include_statistics"
                className="ml-2 text-sm text-secondary-foreground"
              >
                {t('exportPage-platform-statistics')}
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="include_user_stats"
                checked={request.include_user_stats}
                onChange={e => updateRequest({ include_user_stats: e.target.checked })}
                className="h-5 w-5 border-border rounded"
              />
              <label
                htmlFor="include_user_stats"
                className="ml-2 text-sm text-secondary-foreground"
              >
                {t('exportPage-per-user-statistics')}
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="include_quality_metrics"
                checked={request.include_quality_metrics}
                onChange={e => updateRequest({ include_quality_metrics: e.target.checked })}
                className="h-5 w-5 border-border rounded"
              />
              <label
                htmlFor="include_quality_metrics"
                className="ml-2 text-sm text-secondary-foreground"
              >
                {t('exportPage-quality-metrics')}
              </label>
            </div>
          </div>
        </div>

        <div className="pt-4">
          <button
            onClick={onExport}
            disabled={loading}
            className="w-full bg-success text-success-foreground px-6 py-3 rounded-lg hover:bg-success-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {loading ? (
              <LoadingSpinner />
            ) : (
              <>
                <ArrowDownTrayIcon className="h-5 w-5" />
                <span>{t('exportPage-export-metadata')}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

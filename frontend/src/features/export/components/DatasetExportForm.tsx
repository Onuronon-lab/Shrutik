import React from 'react';
import { ArrowDownTrayIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import { DatasetExportRequest } from '../../../types/export';
import LoadingSpinner from '../../../components/common/LoadingSpinner';

interface DatasetExportFormProps {
  request: DatasetExportRequest;
  onRequestChange: (updater: (prev: DatasetExportRequest) => DatasetExportRequest) => void;
  onExport: () => void;
  loading: boolean;
  t: TFunction<'translation'>;
}

export const DatasetExportForm: React.FC<DatasetExportFormProps> = ({
  request,
  onRequestChange,
  onExport,
  loading,
  t,
}) => {
  const updateRequest = (partial: Partial<DatasetExportRequest>) => {
    onRequestChange(prev => ({ ...prev, ...partial }));
  };

  const updateQualityFilters = (partial: NonNullable<DatasetExportRequest['quality_filters']>) => {
    onRequestChange(prev => ({
      ...prev,
      quality_filters: {
        consensus_only: prev.quality_filters?.consensus_only || false,
        validated_only: prev.quality_filters?.validated_only || false,
        ...prev.quality_filters,
        ...partial,
      },
    }));
  };

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
        <DocumentArrowDownIcon className="h-6 w-6 text-primary mr-2" />
        {t('dataExport-exportButton')}
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              {t('dataExport-format')}
            </label>
            <select
              value={request.format}
              onChange={e =>
                updateRequest({ format: e.target.value as DatasetExportRequest['format'] })
              }
              className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
            >
              <option value="json">{t('export-json')}</option>
              <option value="csv">{t('export-csv')}</option>
              <option value="jsonl">{t('export-jsonl')}</option>
              <option value="parquet">{t('export-parquet')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-foreground mb-3">
              {t('dataExport-qualityFilters')}
            </label>
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="consensus_only"
                  checked={request.quality_filters?.consensus_only || false}
                  onChange={e => updateQualityFilters({ consensus_only: e.target.checked })}
                  className="h-4 w-4 text-primary focus:ring-ring border-ring rounded"
                />
                <label htmlFor="consensus_only" className="ml-2 text-sm text-secondary-foreground">
                  {t('dataExport-consensusOnly')}
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="validated_only"
                  checked={request.quality_filters?.validated_only || false}
                  onChange={e => updateQualityFilters({ validated_only: e.target.checked })}
                  className="h-4 w-4 text-primary focus:ring-ring border-ring rounded"
                />
                <label htmlFor="validated_only" className="ml-2 text-sm text-secondary-foreground">
                  {t('dataExport-validatedOnly')}
                </label>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-secondary-foreground mb-1">
                    {t('dataExport-minConfidence')}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={request.quality_filters?.min_confidence ?? ''}
                    onChange={e =>
                      updateQualityFilters({
                        min_confidence: e.target.value ? parseFloat(e.target.value) : undefined,
                      })
                    }
                    className="w-full px-2 py-1 text-sm border border-border rounded focus:ring-1 focus:ring-ring"
                    placeholder="0.0-1.0"
                  />
                </div>
                <div>
                  <label className="block text-xs text-secondary-foreground mb-1">
                    {t('dataExport-minQuality')}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={request.quality_filters?.min_quality ?? ''}
                    onChange={e =>
                      updateQualityFilters({
                        min_quality: e.target.value ? parseFloat(e.target.value) : undefined,
                      })
                    }
                    className="w-full px-2 py-1 text-sm border border-border rounded focus:ring-1 focus:ring-ring"
                    placeholder="0.0-1.0"
                  />
                </div>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('dataExport-dateRange')}
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-secondary-foreground mb-1">
                  {t('dataExport-from')}
                </label>
                <input
                  type="date"
                  value={request.date_from || ''}
                  onChange={e => updateRequest({ date_from: e.target.value || undefined })}
                  className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                />
              </div>
              <div>
                <label className="block text-xs text-secondary-foreground mb-1">
                  {t('dataExport-to')}
                </label>
                <input
                  type="date"
                  value={request.date_to || ''}
                  onChange={e => updateRequest({ date_to: e.target.value || undefined })}
                  className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-foreground mb-2">
              {t('dataExport-maxRecords')}
            </label>
            <input
              type="number"
              min="1"
              value={request.max_records ?? ''}
              onChange={e =>
                updateRequest({
                  max_records: e.target.value ? parseInt(e.target.value, 10) : undefined,
                })
              }
              className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
              placeholder={t('leave-empt-for-all-records')}
            />
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-secondary-foreground mb-3">
              {t('dataExport-includeOptions')}
            </label>
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="include_metadata"
                  checked={request.include_metadata}
                  onChange={e => updateRequest({ include_metadata: e.target.checked })}
                  className="h-4 w-4 text-primary focus:ring-ring border-border rounded"
                />
                <label
                  htmlFor="include_metadata"
                  className="ml-2 text-sm text-secondary-foreground"
                >
                  {t('dataExport-includeMetadata')}
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="include_audio_paths"
                  checked={request.include_audio_paths}
                  onChange={e => updateRequest({ include_audio_paths: e.target.checked })}
                  className="h-4 w-4 text-primary focus:ring-ring border-border rounded"
                />
                <label
                  htmlFor="include_audio_paths"
                  className="ml-2 text-sm text-secondary-foreground"
                >
                  {t('dataExport-includeAudioPaths')}
                </label>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={onExport}
              disabled={loading}
              className="w-full bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <LoadingSpinner />
              ) : (
                <>
                  <ArrowDownTrayIcon className="h-5 w-5" />
                  <span>{t('dataExport-exportButton')}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

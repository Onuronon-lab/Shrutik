import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowDownTrayIcon,
  DocumentArrowDownIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ChartBarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import {
  DatasetExportRequest,
  MetadataExportRequest,
  DatasetExportResponse,
  MetadataExportResponse,
  ExportHistoryResponse
} from '../../types/export';
import LoadingSpinner from '../common/LoadingSpinner';

type ExportTab = 'dataset' | 'metadata' | 'history';

const DataExport: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<ExportTab>('dataset');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Dataset export state
  const [datasetRequest, setDatasetRequest] = useState<DatasetExportRequest>({
    format: 'json',
    quality_filters: {
      consensus_only: false,
      validated_only: false
    },
    include_metadata: true,
    include_audio_paths: true
  });
  
  // Metadata export state
  const [metadataRequest, setMetadataRequest] = useState<MetadataExportRequest>({
    format: 'json',
    include_statistics: true,
    include_user_stats: false,
    include_quality_metrics: true
  });
  
  // Export history state
  const [exportHistory, setExportHistory] = useState<ExportHistoryResponse | null>(null);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyFilters, setHistoryFilters] = useState({
    export_type: '',
    date_from: '',
    date_to: ''
  });
  
  // Platform statistics
  const [platformStats, setPlatformStats] = useState<any>(null);

  const loadInitialData = async () => {
    try {
      const statsData = await apiService.getExportStatistics();
      setPlatformStats(statsData);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const loadExportHistory = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: historyPage,
        page_size: 20,
        ...(historyFilters.export_type && { export_type: historyFilters.export_type }),
        ...(historyFilters.date_from && { date_from: historyFilters.date_from }),
        ...(historyFilters.date_to && { date_to: historyFilters.date_to })
      };
      const historyData = await apiService.getExportHistory(params);
      setExportHistory(historyData);
    } catch (err) {
      setError('Failed to load export history');
      console.error('Export history error:', err);
    } finally {
      setLoading(false);
    }
  }, [historyPage, historyFilters]);

  useEffect(() => {
    if (user?.role === 'sworik_developer') {
      loadInitialData();
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === 'history') {
      loadExportHistory();
    }
  }, [activeTab, historyPage, historyFilters, loadExportHistory]);

  const handleDatasetExport = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response: DatasetExportResponse = await apiService.exportDataset(datasetRequest);
      
      // Create and download file
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: getContentType(datasetRequest.format)
      });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dataset_export_${response.export_id}.${datasetRequest.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      setSuccess(`Dataset exported successfully! ${response.total_records} records exported.`);
      
      // Refresh history if on history tab
      if (activeTab === 'history') {
        loadExportHistory();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export dataset');
      console.error('Dataset export error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMetadataExport = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response: MetadataExportResponse = await apiService.exportMetadata(metadataRequest);
      
      // Create and download file
      const exportData = {
        statistics: response.statistics,
        platform_metrics: response.platform_metrics,
        ...(response.user_statistics && { user_statistics: response.user_statistics }),
        ...(response.quality_metrics && { quality_metrics: response.quality_metrics })
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: getContentType(metadataRequest.format)
      });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `metadata_export_${response.export_id}.${metadataRequest.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      setSuccess('Metadata exported successfully!');
      
      // Refresh history if on history tab
      if (activeTab === 'history') {
        loadExportHistory();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export metadata');
      console.error('Metadata export error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getContentType = (format: string): string => {
    switch (format) {
      case 'json': return 'application/json';
      case 'csv': return 'text/csv';
      case 'jsonl': return 'application/jsonl';
      case 'parquet': return 'application/octet-stream';
      default: return 'application/json';
    }
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
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
            <h3 className="text-lg font-medium text-destructive-foreground">Access Denied</h3>
            <p className="text-destructive-foreground mt-1">
              Data export functionality is restricted to Admins and Sworik developers only.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'dataset' as ExportTab, name: 'Dataset Export', icon: DocumentArrowDownIcon },
    { id: 'metadata' as ExportTab, name: 'Metadata Export', icon: ChartBarIcon },
    { id: 'history' as ExportTab, name: 'Export History', icon: ClockIcon }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <ArrowDownTrayIcon className="mx-auto h-16 w-16 text-primary mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-2">Data Export</h1>
        <p className="text-secondary-foreground">
          Export validated datasets and platform metadata for AI training
        </p>
      </div>

      {/* Platform Statistics Overview */}
      {platformStats && (
        <div className="bg-card rounded-lg shadow-md p-6 mb-8 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
            <InformationCircleIcon className="h-6 w-6 text-primary mr-2" />
            Platform Overview
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">{platformStats.statistics?.total_recordings || 0}</p>
              <p className="text-sm text-secondary-foreground">Total Recordings</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">{platformStats.statistics?.total_chunks || 0}</p>
              <p className="text-sm text-secondary-foreground">Audio Chunks</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">{platformStats.statistics?.total_transcriptions || 0}</p>
              <p className="text-sm text-secondary-foreground">Transcriptions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">{platformStats.statistics?.validated_transcriptions || 0}</p>
              <p className="text-sm text-secondary-foreground">Validated</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-border mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
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

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-destructive border border-destructive-border rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-destructive">{error}</p>
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

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'dataset' && (
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
              <DocumentArrowDownIcon className="h-6 w-6 text-primary mr-2" />
              Export Dataset
            </h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Export Configuration */}
              <div className="space-y-6">
                {/* Format Selection */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Export Format
                  </label>
                  <select
                    value={datasetRequest.format}
                    onChange={(e) => setDatasetRequest(prev => ({ 
                      ...prev, 
                      format: e.target.value as any 
                    }))}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                  >
                    <option value="json">JSON - Standard format with nested structure</option>
                    <option value="csv">CSV - Comma-separated values (flattened)</option>
                    <option value="jsonl">JSON Lines - One JSON object per line</option>
                    <option value="parquet">Parquet - Columnar format for analytics</option>
                  </select>
                </div>

                {/* Quality Filters */}
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-3">
                    Quality Filters
                  </label>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="consensus_only"
                        checked={datasetRequest.quality_filters?.consensus_only || false}
                        onChange={(e) => setDatasetRequest(prev => ({
                          ...prev,
                          quality_filters: {
                            ...prev.quality_filters,
                            consensus_only: e.target.checked,
                            validated_only: prev.quality_filters?.validated_only || false
                          }
                        }))}
                        className="h-4 w-4 text-primary focus:ring-ring border-ring rounded"
                      />
                      <label htmlFor="consensus_only" className="ml-2 text-sm text-secondary-foreground">
                        Consensus transcriptions only
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="validated_only"
                        checked={datasetRequest.quality_filters?.validated_only || false}
                        onChange={(e) => setDatasetRequest(prev => ({
                          ...prev,
                          quality_filters: {
                            ...prev.quality_filters,
                            validated_only: e.target.checked,
                            consensus_only: prev.quality_filters?.consensus_only || false
                          }
                        }))}
                        className="h-4 w-4 text-primary focus:ring-ring border-ring rounded"
                      />
                      <label htmlFor="validated_only" className="ml-2 text-sm text-secondary-foreground">
                        Validated transcriptions only
                      </label>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-secondary-foreground mb-1">Min Confidence</label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.1"
                          value={datasetRequest.quality_filters?.min_confidence || ''}
                          onChange={(e) => setDatasetRequest(prev => ({
                            ...prev,
                            quality_filters: {
                              ...prev.quality_filters,
                              min_confidence: e.target.value ? parseFloat(e.target.value) : undefined,
                              consensus_only: prev.quality_filters?.consensus_only || false,
                              validated_only: prev.quality_filters?.validated_only || false
                            }
                          }))}
                          className="w-full px-2 py-1 text-sm border border-border rounded focus:ring-1 focus:ring-ring"
                          placeholder="0.0-1.0"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-secondary-foreground mb-1">Min Quality</label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.1"
                          value={datasetRequest.quality_filters?.min_quality || ''}
                          onChange={(e) => setDatasetRequest(prev => ({
                            ...prev,
                            quality_filters: {
                              ...prev.quality_filters,
                              min_quality: e.target.value ? parseFloat(e.target.value) : undefined,
                              consensus_only: prev.quality_filters?.consensus_only || false,
                              validated_only: prev.quality_filters?.validated_only || false
                            }
                          }))}
                          className="w-full px-2 py-1 text-sm border border-border rounded focus:ring-1 focus:ring-ring"
                          placeholder="0.0-1.0"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Range (Optional)
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-secondary-foreground mb-1">From</label>
                      <input
                        type="date"
                        value={datasetRequest.date_from || ''}
                        onChange={(e) => setDatasetRequest(prev => ({ 
                          ...prev, 
                          date_from: e.target.value || undefined 
                        }))}
                        className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-secondary-foreground mb-1">To</label>
                      <input
                        type="date"
                        value={datasetRequest.date_to || ''}
                        onChange={(e) => setDatasetRequest(prev => ({ 
                          ...prev, 
                          date_to: e.target.value || undefined 
                        }))}
                        className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                      />
                    </div>
                  </div>
                </div>

                {/* Max Records */}
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-2">
                    Maximum Records (Optional)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={datasetRequest.max_records || ''}
                    onChange={(e) => setDatasetRequest(prev => ({ 
                      ...prev, 
                      max_records: e.target.value ? parseInt(e.target.value) : undefined 
                    }))}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                    placeholder="Leave empty for all records"
                  />
                </div>
              </div>

              {/* Export Options */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-3">
                    Include Options
                  </label>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="include_metadata"
                        checked={datasetRequest.include_metadata}
                        onChange={(e) => setDatasetRequest(prev => ({ 
                          ...prev, 
                          include_metadata: e.target.checked 
                        }))}
                        className="h-4 w-4 text-primary focus:ring-ring border-border rounded"
                      />
                      <label htmlFor="include_metadata" className="ml-2 text-sm text-secondary-foreground">
                        Include detailed metadata
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="include_audio_paths"
                        checked={datasetRequest.include_audio_paths}
                        onChange={(e) => setDatasetRequest(prev => ({ 
                          ...prev, 
                          include_audio_paths: e.target.checked 
                        }))}
                        className="h-4 w-4 text-primary focus:ring-ring border-border rounded"
                      />
                      <label htmlFor="include_audio_paths" className="ml-2 text-sm text-secondary-foreground">
                        Include audio file paths
                      </label>
                    </div>
                  </div>
                </div>

                {/* Export Button */}
                <div className="pt-4">
                  <button
                    onClick={handleDatasetExport}
                    disabled={loading}
                    className="w-full bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {loading ? (
                      <LoadingSpinner />
                    ) : (
                      <>
                        <ArrowDownTrayIcon className="h-5 w-5" />
                        <span>Export Dataset</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'metadata' && (
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
              <ChartBarIcon className="h-6 w-6 text-success mr-2" />
              Export Metadata
            </h3>
            
            <div className="max-w-md mx-auto space-y-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-secondary-foreground mb-2">
                  Export Format
                </label>
                <select
                  value={metadataRequest.format}
                  onChange={(e) => setMetadataRequest(prev => ({ 
                    ...prev, 
                    format: e.target.value as any 
                  }))}
                  className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                >
                  <option value="json">JSON - Standard format</option>
                  <option value="csv">CSV - Comma-separated values</option>
                </select>
              </div>

              {/* Include Options */}
              <div>
                <label className="block text-sm font-medium text-secondary-foreground mb-3">
                  Include Options
                </label>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="include_statistics"
                      checked={metadataRequest.include_statistics}
                      onChange={(e) => setMetadataRequest(prev => ({ 
                        ...prev, 
                        include_statistics: e.target.checked 
                      }))}
                      className="h-5 w-5 border-border rounded"
                    />
                    <label htmlFor="include_statistics" className="ml-2 text-sm text-secondary-foreground">
                      Platform statistics
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="include_user_stats"
                      checked={metadataRequest.include_user_stats}
                      onChange={(e) => setMetadataRequest(prev => ({ 
                        ...prev, 
                        include_user_stats: e.target.checked 
                      }))}
                      className="h-5 w-5 border-border rounded"
                    />
                    <label htmlFor="include_user_stats" className="ml-2 text-sm text-secondary-foreground">
                      Per-user statistics
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="include_quality_metrics"
                      checked={metadataRequest.include_quality_metrics}
                      onChange={(e) => setMetadataRequest(prev => ({ 
                        ...prev, 
                        include_quality_metrics: e.target.checked 
                      }))}
                      className="h-5 w-5 border-border rounded"
                    />
                    <label htmlFor="include_quality_metrics" className="ml-2 text-sm text-secondary-foreground">
                      Quality metrics
                    </label>
                  </div>
                </div>
              </div>

              {/* Export Button */}
              <div className="pt-4">
                <button
                  onClick={handleMetadataExport}
                  disabled={loading}
                  className="w-full bg-success text-success-foreground px-6 py-3 rounded-lg hover:bg-success-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {loading ? (
                    <LoadingSpinner />
                  ) : (
                    <>
                      <ArrowDownTrayIcon className="h-5 w-5" />
                      <span>Export Metadata</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="bg-card rounded-lg shadow-md border border-border">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold text-foreground flex items-center">
                <ClockIcon className="h-6 w-6 text-info mr-2" />
                Export History
              </h3>
              
              {/* History Filters */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-1">
                    Export Type
                  </label>
                  <select
                    value={historyFilters.export_type}
                    onChange={(e) => setHistoryFilters(prev => ({ 
                      ...prev, 
                      export_type: e.target.value 
                    }))}
                    className="w-full px-3 py-3 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                  >
                    <option value="">All Types</option>
                    <option value="dataset">Dataset</option>
                    <option value="metadata">Metadata</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-1">
                    From Date
                  </label>
                  <input
                    type="date"
                    value={historyFilters.date_from}
                    onChange={(e) => setHistoryFilters(prev => ({ 
                      ...prev, 
                      date_from: e.target.value 
                    }))}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-1">
                    To Date
                  </label>
                  <input
                    type="date"
                    value={historyFilters.date_to}
                    onChange={(e) => setHistoryFilters(prev => ({ 
                      ...prev, 
                      date_to: e.target.value 
                    }))}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
                  />
                </div>
              </div>
            </div>

            {/* History Table */}
            <div className="overflow-x-auto">
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <LoadingSpinner />
                </div>
              ) : exportHistory?.logs.length ? (
                <table className="min-w-full divide-y divide-border">
                  <thead className="bg-background">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Export ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Format
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Records
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-mutated-foreground uppercase tracking-wider">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-card divide-y divide-border">
                    {exportHistory.logs.map((log) => (
                      <tr key={log.id} className="hover:bg-background">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                          {log.export_id.substring(0, 8)}...
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            log.export_type === 'dataset' 
                              ? 'bg-primary text-primary-foreground' 
                              : 'bg-success text-primary-foreground'
                          }`}>
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
                  <h3 className="mt-2 text-sm font-medium text-foreground">No export history</h3>
                  <p className="mt-1 text-sm text-secondary-foreground">
                    No exports have been performed yet.
                  </p>
                </div>
              )}
            </div>

            {/* Pagination */}
            {exportHistory && exportHistory.total_count > 20 && (
              <div className="px-6 py-3 border-t border-border flex items-center justify-between">
                <div className="text-sm text-secondary-foreground">
                  Showing {((historyPage - 1) * 20) + 1} to {Math.min(historyPage * 20, exportHistory.total_count)} of {exportHistory.total_count} results
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setHistoryPage(prev => Math.max(1, prev - 1))}
                    disabled={historyPage === 1}
                    className="px-3 py-1 border border-border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-background"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setHistoryPage(prev => prev + 1)}
                    disabled={historyPage * 20 >= exportHistory.total_count}
                    className="px-3 py-1 border border-border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-background"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DataExport;
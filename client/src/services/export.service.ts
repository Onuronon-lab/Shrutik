import { apiClient } from './apiClient';
import { DatasetExportRequest, MetadataExportRequest } from '../types/export';

export const exportService = {
  async exportDataset(request: DatasetExportRequest): Promise<any> {
    return apiClient.post('/export/dataset', request);
  },

  async exportMetadata(request: MetadataExportRequest): Promise<any> {
    return apiClient.post('/export/metadata', request);
  },

  async getExportHistory(params?: {
    user_id?: number;
    export_type?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    const queryString = searchParams.toString();
    return apiClient.get(`/export/history${queryString ? `?${queryString}` : ''}`);
  },

  async getSupportedExportFormats(): Promise<any> {
    return apiClient.get('/export/formats');
  },

  async getExportStatistics(): Promise<any> {
    return apiClient.get('/export/stats');
  },

  async createExportBatch(filters?: {
    date_from?: string;
    date_to?: string;
    min_duration?: number;
    max_duration?: number;
    force_create?: boolean;
  }): Promise<any> {
    const requestBody: any = {
      force_create: filters?.force_create ?? true,
    };

    if (filters) {
      if (filters.date_from) requestBody.date_from = filters.date_from;
      if (filters.date_to) requestBody.date_to = filters.date_to;
      if (filters.min_duration !== undefined) requestBody.min_duration = filters.min_duration;
      if (filters.max_duration !== undefined) requestBody.max_duration = filters.max_duration;
    }

    return apiClient.post('/export/batch/create', requestBody);
  },

  async getExportBatch(batchId: string): Promise<any> {
    return apiClient.get(`/export/batch/${batchId}`);
  },

  async listExportBatches(params?: {
    page?: number;
    page_size?: number;
    status_filter?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params) {
      if (params.page !== undefined) searchParams.append('page', params.page.toString());
      if (params.page_size !== undefined)
        searchParams.append('page_size', params.page_size.toString());
      if (params.status_filter) searchParams.append('status_filter', params.status_filter);
      if (params.date_from) searchParams.append('date_from', params.date_from);
      if (params.date_to) searchParams.append('date_to', params.date_to);
    }
    return apiClient.get(`/export/batch/list?${searchParams.toString()}`);
  },

  async downloadExportBatch(batchId: string): Promise<any> {
    return apiClient.getBlob(`/export/batch/${batchId}/download`);
  },

  async getDownloadQuota(): Promise<any> {
    return apiClient.get('/export/batch/download/quota');
  },

  async retryExportBatch(batchId: string): Promise<any> {
    return apiClient.post(`/export/batch/${batchId}/retry`);
  },
};

export interface ExportBatch {
  batch_id: string;
  status: ExportBatchStatus;
  storage_type: 'local' | 'r2';
  chunk_count: number;
  file_size_bytes?: number;
  created_at: string;
  completed_at?: string;
  filter_criteria?: Record<string, unknown>;
}

export type ExportBatchStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DownloadQuota {
  downloads_today: number;
  downloads_remaining: number;
  daily_limit: number;
  reset_time: string;
}

export interface CreateBatchFormValues {
  date_from: string;
  date_to: string;
  min_duration: string;
  max_duration: string;
  force_create: boolean;
}

export interface ExportBatchListResponse {
  batches: ExportBatch[];
  total_count: number;
  page: number;
  page_size: number;
}

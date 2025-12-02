export interface ExportFormat {
  value: 'json' | 'csv' | 'jsonl' | 'parquet';
  label: string;
  description: string;
  mimeType: string;
  fileExtension: string;
}

export interface QualityFilters {
  min_confidence?: number;
  min_quality?: number;
  consensus_only?: boolean;
  validated_only?: boolean;
}

export interface DatasetExportRequest {
  format: 'json' | 'csv' | 'jsonl' | 'parquet';
  quality_filters?: QualityFilters;
  language_ids?: number[];
  user_ids?: number[];
  date_from?: string;
  date_to?: string;
  include_metadata: boolean;
  include_audio_paths: boolean;
  max_records?: number;
}

export interface MetadataExportRequest {
  format: 'json' | 'csv';
  include_statistics: boolean;
  include_user_stats: boolean;
  include_quality_metrics: boolean;
}

export interface ExportedDataItem {
  chunk_id: number;
  recording_id: number;
  audio_file_path: string;
  chunk_file_path: string;
  transcription_text: string;
  transcription_id: number;
  contributor_id: number;
  language_id: number;
  language_name: string;
  quality_score: number;
  confidence_score: number;
  is_consensus: boolean;
  is_validated: boolean;
  recording_duration: number;
  chunk_duration: number;
  chunk_start_time: number;
  chunk_end_time: number;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface ExportStatistics {
  total_recordings: number;
  total_chunks: number;
  total_transcriptions: number;
  consensus_transcriptions: number;
  validated_transcriptions: number;
  unique_contributors: number;
  languages: Array<{ id: number; name: string }>;
  quality_distribution: Record<string, number>;
  export_timestamp: string;
  filters_applied: Record<string, any>;
}

export interface DatasetExportResponse {
  export_id: string;
  data: ExportedDataItem[];
  statistics: ExportStatistics;
  format: string;
  total_records: number;
  export_timestamp: string;
}

export interface MetadataExportResponse {
  export_id: string;
  statistics: ExportStatistics;
  platform_metrics: Record<string, any>;
  user_statistics?: Array<Record<string, any>>;
  quality_metrics?: Record<string, any>;
  format: string;
  export_timestamp: string;
}

export interface ExportAuditLog {
  id: number;
  export_id: string;
  user_id: number;
  user_email: string;
  export_type: 'dataset' | 'metadata';
  format: string;
  filters_applied: Record<string, any>;
  records_exported: number;
  file_size_bytes?: number;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface ExportHistoryResponse {
  logs: ExportAuditLog[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface ExportProgress {
  export_id: string;
  status: 'preparing' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  estimated_completion?: string;
  error_message?: string;
}

export interface ExportBatch {
  id: number;
  batch_id: string;
  archive_path: string;
  storage_type: 'local' | 'r2';
  chunk_count: number;
  file_size_bytes?: number;
  chunk_ids: number[];
  status: ExportBatchStatus;
  exported: boolean;
  error_message?: string;
  retry_count: number;
  checksum?: string;
  compression_level?: number;
  format_version: string;
  recording_id_range?: Record<string, any>;
  language_stats?: Record<string, any>;
  total_duration_seconds?: number;
  filter_criteria?: Record<string, any>;
  created_at: string;
  completed_at?: string;
  created_by_id?: number;
}

export type ExportBatchStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DownloadQuota {
  downloads_today: number;
  downloads_remaining: number;
  daily_limit: number;
  reset_time: string | null; // null for unlimited users
  user_role: string;
  is_unlimited: boolean;
}

export interface CreateBatchFormValues {
  date_from: string;
  date_to: string;
  min_duration: string;
  max_duration: string;
  force_create: boolean;
}

export interface ExportBatchCreateRequest {
  date_from?: string; // ISO date string
  date_to?: string; // ISO date string
  min_duration?: number;
  max_duration?: number;
  force_create: boolean;
}

export interface ExportBatchListResponse {
  batches: ExportBatch[];
  total_count: number;
  page: number;
  page_size: number;
}

// Enhanced Error Response Types

export interface ErrorDetails {
  available_chunks?: number;
  required_chunks?: number;
  user_role?: string;
  downloads_today?: number;
  daily_limit?: number;
  reset_time?: string; // ISO format string
  hours_until_reset?: number;
  suggestions: string[];
}

export interface StructuredErrorResponse {
  error: string;
  details: ErrorDetails;
}

// Type guards for error handling
export function isStructuredError(error: any): error is StructuredErrorResponse {
  return error && typeof error === 'object' && 'error' in error && 'details' in error;
}

export function hasErrorSuggestions(error: any): boolean {
  return (
    isStructuredError(error) &&
    Array.isArray(error.details.suggestions) &&
    error.details.suggestions.length > 0
  );
}

// Utility functions for error handling
export function getErrorMessage(error: any): string {
  if (isStructuredError(error)) {
    return error.error;
  }
  if (error?.message) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unexpected error occurred';
}

export function getErrorSuggestions(error: any): string[] {
  if (isStructuredError(error)) {
    return error.details.suggestions || [];
  }
  return [];
}

export function getErrorContext(error: any): Partial<ErrorDetails> {
  if (isStructuredError(error)) {
    return error.details;
  }
  return {};
}

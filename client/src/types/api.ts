export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
  // Enhanced error structure for export operations
  error?: string;
  structured_details?: {
    available_chunks?: number;
    required_chunks?: number;
    user_role?: string;
    downloads_today?: number;
    daily_limit?: number;
    reset_time?: string;
    hours_until_reset?: number;
    suggestions?: string[];
  };
}

// Script related types
export type DurationCategory = '2_minutes' | '5_minutes' | '10_minutes';

export interface Script {
  id: number;
  text: string;
  duration_category: DurationCategory;
  language_id: number;
  meta_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface RandomScriptRequest {
  duration_category: DurationCategory;
  language_id?: number;
}

// Recording related types
export interface RecordingSession {
  session_id: string;
  script_id: number;
  script_text: string;
  language_id: number;
  expected_duration_category: string;
  created_at: string;
  expires_at: string;
}

export interface RecordingUpload {
  session_id: string;
  duration: number;
  audio_format: string;
  sample_rate?: number;
  channels?: number;
  bit_depth?: number;
  file_size: number;
}

export interface VoiceRecording {
  id: number;
  user_id: number;
  script_id: number;
  language_id: number;
  file_path: string;
  duration: number;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  meta_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface RecordingProgress {
  recording_id: number;
  status: string;
  progress_percentage: number;
  message: string;
  estimated_completion?: string;
}

// Transcription related types
export interface AudioChunk {
  id: number;
  recording_id: number;
  chunk_index: number;
  file_path: string;
  start_time: number;
  end_time: number;
  duration: number;
  sentence_hint?: string;
  meta_data: Record<string, any>;
  created_at: string;
}

export interface Transcription {
  id: number;
  chunk_id: number;
  user_id: number;
  text: string;
  language_id: number;
  quality?: number;
  confidence?: number;
  created_at: string;
}

export interface TranscriptionSession {
  chunks: AudioChunk[];
  total_count: number;
  session_id: string;
}

export interface TranscriptionCreate {
  chunk_id: number;
  text: string;
  language_id: number;
}

export interface TranscriptionSubmission {
  session_id: string;
  transcriptions: TranscriptionCreate[];
  skipped_chunk_ids?: number[];
}

// Admin related types
export interface PlatformStats {
  total_users: number;
  total_contributors: number;
  total_admins: number;
  total_sworik_developers: number;
  total_recordings: number;
  total_chunks: number;
  total_transcriptions: number;
  total_validated_transcriptions: number;
  total_quality_reviews: number;
  avg_recording_duration?: number;
  avg_transcription_quality?: number;
  recordings_by_status: Record<string, number>;
  transcriptions_by_validation_status: Record<string, number>;
}

export interface UserStats {
  user_id: number;
  name: string;
  email: string;
  role: string;
  recordings_count: number;
  transcriptions_count: number;
  quality_reviews_count: number;
  avg_transcription_quality?: number;
  created_at: string;
}

export interface UserManagement {
  id: number;
  name: string;
  email: string;
  role: string;
  recordings_count: number;
  transcriptions_count: number;
  quality_reviews_count: number;
  created_at: string;
  last_activity?: string;
}

export interface QualityReviewItem {
  id: number;
  transcription_id: number;
  chunk_id: number;
  transcription_text: string;
  contributor_name: string;
  contributor_id: number;
  decision: string;
  rating?: number;
  comment?: string;
  reviewer_name?: string;
  created_at: string;
  chunk_file_path: string;
}

export interface FlaggedTranscription {
  transcription_id: number;
  chunk_id: number;
  text: string;
  contributor_name: string;
  contributor_id: number;
  quality_score: number;
  confidence_score: number;
  chunk_file_path: string;
  created_at: string;
  review_count: number;
}

export interface SystemHealth {
  database_status: string;
  total_storage_used?: number;
  active_users_last_24h: number;
  active_users_last_7d: number;
  processing_queue_size: number;
  failed_recordings_count: number;
  avg_response_time?: number;
  uptime?: string;
}

export interface UsageAnalytics {
  daily_recordings: Array<{ date: string; count: number }>;
  daily_transcriptions: Array<{ date: string; count: number }>;
  user_activity_by_role: Record<string, number>;
  popular_script_durations: Record<string, number>;
  transcription_quality_trend: Array<{ date: string; quality: number }>;
  top_contributors: Array<{ user_id: number; name: string; contribution_count: number }>;
}

export interface ScriptValidation {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  estimated_duration?: number;
  word_count: number;
  character_count: number;
}

export interface ScriptListResponse {
  scripts: Script[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface CurrentUserStats {
  recordings_count: number;
  transcriptions_count: number;
  quality_reviews_count: number;
  avg_transcription_quality?: number;
}

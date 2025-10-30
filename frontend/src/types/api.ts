export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
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
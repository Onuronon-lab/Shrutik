// State type definitions for Zustand stores

import { Script, RecordingSession } from './api';
import {
  RecordingStatus,
  UploadState,
  ScriptLoadingState,
  StrictDurationOption,
  DeepReadonly,
} from './enhanced';

// Re-export enhanced types for backward compatibility
export type { RecordingStatus, UploadState } from './enhanced';

// Duration option type (enhanced version)
export type DurationOption = StrictDurationOption;

// Enhanced Recording state with strict typing
export interface RecordingState {
  readonly status: RecordingStatus;
  readonly recordingTime: number;
  readonly audioBlob: Blob | null;
  readonly audioUrl: string | null;
  readonly mediaRecorder: MediaRecorder | null;
  readonly stream: MediaStream | null;
  readonly error: string | null;
}

// Enhanced Script state with discriminated union
export interface ScriptState {
  readonly loadingState: ScriptLoadingState;
  readonly selectedDuration: DurationOption | null;
  readonly cache: DeepReadonly<Map<string, Script>>;
}

// Enhanced Session state with strict typing
export interface SessionState {
  readonly current: RecordingSession | null;
  readonly isCreating: boolean;
  readonly error: string | null;
  readonly createdAt: number | null;
  readonly expiresAt: number | null;
}

// Enhanced Upload state wrapper
export interface UploadStateWrapper {
  readonly state: UploadState;
  readonly history: DeepReadonly<
    Array<{
      timestamp: number;
      status: UploadState['status'];
      error?: string;
    }>
  >;
}

// Global app state combining all stores with enhanced typing
export interface AppState {
  readonly recording: RecordingState;
  readonly script: ScriptState;
  readonly upload: UploadStateWrapper;
  readonly session: SessionState;
  readonly lastUpdated: number;
}

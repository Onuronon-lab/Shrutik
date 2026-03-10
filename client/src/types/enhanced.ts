// Enhanced TypeScript types with discriminated unions and utility types

import { Script, VoiceRecording } from './api';

// ============================================================================
// DISCRIMINATED UNIONS FOR VARIANT TYPES
// ============================================================================

// Enhanced RecordingStatus with discriminated unions
export type RecordingStatus =
  | { type: 'idle' }
  | { type: 'initializing'; message: string }
  | { type: 'recording'; startTime: number; duration: number }
  | { type: 'paused'; pausedAt: number; totalDuration: number }
  | { type: 'completed'; blob: Blob; duration: number; url: string }
  | { type: 'error'; error: string; code?: string };

// Enhanced UploadState with discriminated unions
export type UploadState =
  | { status: 'idle' }
  | { status: 'preparing'; message: string }
  | { status: 'uploading'; progress: number; bytesUploaded: number; totalBytes: number }
  | { status: 'processing'; message: string }
  | { status: 'success'; recording: VoiceRecording; uploadTime: number }
  | { status: 'error'; error: string; code?: string; retryable: boolean };

// Script loading state with discriminated unions
export type ScriptLoadingState =
  | { status: 'idle' }
  | { status: 'loading'; duration: string }
  | { status: 'loaded'; script: Script; loadTime: number }
  | { status: 'error'; error: string; retryCount: number };

// Network request state
export type NetworkState<T> =
  | { status: 'idle' }
  | { status: 'loading'; signal?: AbortSignal }
  | { status: 'success'; data: T; timestamp: number }
  | { status: 'error'; error: string; statusCode?: number };

// ============================================================================
// UTILITY TYPES FOR STATE TRANSFORMATIONS AND COMPONENT PROPS
// ============================================================================

// Base component props with common attributes
export type BaseComponentProps = {
  className?: string;
  'data-testid'?: string;
  id?: string;
};

// Generic component props wrapper
export type ComponentProps<T = {}> = T & BaseComponentProps;

// Event handler utility types
export type EventHandler<T = Event> = (event: T) => void;
export type AsyncEventHandler<T = Event> = (event: T) => Promise<void>;

// Form field props utility type
export type FormFieldProps<T> = ComponentProps<{
  value: T;
  onChange: (value: T) => void;
  onBlur?: () => void;
  disabled?: boolean;
  required?: boolean;
  error?: string;
}>;

// Button variant utility type
export type ButtonVariant = 'primary' | 'secondary' | 'destructive' | 'success' | 'warning';
export type ButtonSize = 'sm' | 'md' | 'lg';

export type ButtonProps = ComponentProps<{
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  onClick?: EventHandler<React.MouseEvent<HTMLButtonElement>>;
  type?: 'button' | 'submit' | 'reset';
  children: React.ReactNode;
}>;

// State transformation utilities
export type StateUpdater<T> = (prevState: T) => T;
export type StateAction<T> = T | StateUpdater<T>;

// Extract specific status from discriminated union
export type ExtractStatus<T, S extends string> = T extends { status: S } ? T : never;
export type ExtractType<T, S extends string> = T extends { type: S } ? T : never;

// Utility to make specific properties required
export type RequireFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Utility to make specific properties optional
export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Deep readonly utility
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};

// ============================================================================
// STRICT API RESPONSE TYPES WITH VALIDATION
// ============================================================================

// Generic API response with strict typing
export interface StrictApiResponse<T> {
  readonly data: T;
  readonly success: true;
  readonly message?: string;
  readonly timestamp: string;
  readonly requestId: string;
}

export interface StrictApiError {
  readonly success: false;
  readonly error: {
    readonly message: string;
    readonly code: string;
    readonly statusCode: number;
    readonly details?: Record<string, unknown>;
  };
  readonly timestamp: string;
  readonly requestId: string;
}

export type StrictApiResult<T> = StrictApiResponse<T> | StrictApiError;

// Type guards for API responses
export const isApiSuccess = <T>(response: StrictApiResult<T>): response is StrictApiResponse<T> => {
  return response.success === true;
};

export const isApiError = <T>(response: StrictApiResult<T>): response is StrictApiError => {
  return response.success === false;
};

// Validated API response types
export interface ValidatedScript extends Omit<Script, 'meta_data'> {
  readonly meta_data: DeepReadonly<{
    word_count: number;
    estimated_duration: number;
    difficulty_level: 'easy' | 'medium' | 'hard';
    tags: readonly string[];
  }>;
}

export interface ValidatedVoiceRecording extends Omit<VoiceRecording, 'meta_data' | 'status'> {
  readonly status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  readonly meta_data: DeepReadonly<{
    file_size: number;
    sample_rate: number;
    channels: number;
    bit_depth: number;
    format: string;
  }>;
}

// ============================================================================
// PRECISE EVENT TYPES FOR ALL EVENT HANDLERS
// ============================================================================

// Mouse event types
export type MouseEventHandler<T = HTMLElement> = EventHandler<React.MouseEvent<T>>;
export type ClickEventHandler<T = HTMLButtonElement> = MouseEventHandler<T>;

// Keyboard event types
export type KeyboardEventHandler<T = HTMLElement> = EventHandler<React.KeyboardEvent<T>>;
export type KeyDownHandler<T = HTMLElement> = KeyboardEventHandler<T>;
export type KeyUpHandler<T = HTMLElement> = KeyboardEventHandler<T>;

// Form event types
export type FormEventHandler<T = HTMLFormElement> = EventHandler<React.FormEvent<T>>;
export type SubmitEventHandler<T = HTMLFormElement> = FormEventHandler<T>;

// Input event types
export type InputEventHandler<T = HTMLInputElement> = EventHandler<React.ChangeEvent<T>>;
export type TextAreaEventHandler = EventHandler<React.ChangeEvent<HTMLTextAreaElement>>;
export type SelectEventHandler = EventHandler<React.ChangeEvent<HTMLSelectElement>>;

// Focus event types
export type FocusEventHandler<T = HTMLElement> = EventHandler<React.FocusEvent<T>>;
export type BlurEventHandler<T = HTMLElement> = FocusEventHandler<T>;

// Media event types
export type MediaEventHandler<T = HTMLMediaElement> = EventHandler<React.SyntheticEvent<T>>;
export type AudioEventHandler = MediaEventHandler<HTMLAudioElement>;

// Custom event types for recording
export interface RecordingStartEvent {
  readonly timestamp: number;
  readonly duration: number;
  readonly quality: 'low' | 'medium' | 'high';
}

export interface RecordingStopEvent {
  readonly timestamp: number;
  readonly duration: number;
  readonly blob: Blob;
  readonly size: number;
}

export interface RecordingErrorEvent {
  readonly timestamp: number;
  readonly error: string;
  readonly code: string;
  readonly recoverable: boolean;
}

export type RecordingEventHandler<T> = (event: T) => void;

// ============================================================================
// COMPONENT-SPECIFIC ENHANCED TYPES
// ============================================================================

// Enhanced Duration Option with strict typing
export interface StrictDurationOption {
  readonly value: '2_minutes' | '5_minutes' | '10_minutes';
  readonly label: string;
  readonly minutes: 2 | 5 | 10;
  readonly description: string;
  readonly maxFileSize: number;
  readonly recommendedFor: readonly string[];
}

// Enhanced Recording Controls Props
export interface EnhancedRecordingControlsProps extends ComponentProps {
  readonly recordingStatus: RecordingStatus;
  readonly selectedDuration: StrictDurationOption | null;
  readonly stream: MediaStream | null;
  readonly onStartRecording: AsyncEventHandler<RecordingStartEvent>;
  readonly onStopRecording: RecordingEventHandler<RecordingStopEvent>;
  readonly onTogglePause: EventHandler;
  readonly onPlayRecording: EventHandler;
  readonly onResetRecording: EventHandler;
  readonly onError?: RecordingEventHandler<RecordingErrorEvent>;
}

// Enhanced Upload Manager Props
export interface EnhancedUploadManagerProps extends ComponentProps {
  readonly uploadState: UploadState;
  readonly onUpload: (blob: Blob, metadata: UploadMetadata) => Promise<void>;
  readonly onCancel?: EventHandler;
  readonly onRetry?: EventHandler;
  readonly maxFileSize: number;
  readonly allowedFormats: readonly string[];
}

export interface UploadMetadata {
  readonly sessionId: string;
  readonly duration: number;
  readonly format: string;
  readonly size: number;
  readonly checksum?: string;
}

// Enhanced Script Viewer Props
export interface EnhancedScriptViewerProps extends ComponentProps {
  readonly scriptState: ScriptLoadingState;
  readonly onScriptLoad?: (script: ValidatedScript) => void;
  readonly onError?: (error: string) => void;
  readonly highlightWords?: boolean;
  readonly fontSize?: 'sm' | 'md' | 'lg';
}

// ============================================================================
// TYPE VALIDATION UTILITIES
// ============================================================================

// Runtime type validation helpers
export const validateRecordingStatus = (status: unknown): status is RecordingStatus => {
  if (typeof status !== 'object' || status === null) return false;
  const s = status as Record<string, unknown>;

  switch (s.type) {
    case 'idle':
      return Object.keys(s).length === 1;
    case 'initializing':
      return typeof s.message === 'string';
    case 'recording':
      return typeof s.startTime === 'number' && typeof s.duration === 'number';
    case 'paused':
      return typeof s.pausedAt === 'number' && typeof s.totalDuration === 'number';
    case 'completed':
      return s.blob instanceof Blob && typeof s.duration === 'number' && typeof s.url === 'string';
    case 'error':
      return typeof s.error === 'string';
    default:
      return false;
  }
};

export const validateUploadState = (state: unknown): state is UploadState => {
  if (typeof state !== 'object' || state === null) return false;
  const s = state as Record<string, unknown>;

  switch (s.status) {
    case 'idle':
      return Object.keys(s).length === 1;
    case 'preparing':
      return typeof s.message === 'string';
    case 'uploading':
      return (
        typeof s.progress === 'number' &&
        typeof s.bytesUploaded === 'number' &&
        typeof s.totalBytes === 'number'
      );
    case 'processing':
      return typeof s.message === 'string';
    case 'success':
      return typeof s.recording === 'object' && typeof s.uploadTime === 'number';
    case 'error':
      return typeof s.error === 'string' && typeof s.retryable === 'boolean';
    default:
      return false;
  }
};

// Type assertion helpers
export const assertRecordingStatus = (status: unknown): RecordingStatus => {
  if (!validateRecordingStatus(status)) {
    throw new Error('Invalid RecordingStatus');
  }
  return status;
};

export const assertUploadState = (state: unknown): UploadState => {
  if (!validateUploadState(state)) {
    throw new Error('Invalid UploadState');
  }
  return state;
};

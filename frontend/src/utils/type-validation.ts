// Type validation and transformation utilities

import {
  RecordingStatus,
  UploadState,
  ScriptLoadingState,
  StrictApiResponse,
  StrictApiError,
  ValidatedVoiceRecording,
  StrictDurationOption,
  NetworkState,
} from '../types/enhanced';

// ============================================================================
// RUNTIME TYPE VALIDATION
// ============================================================================

/**
 * Validates if a value matches the RecordingStatus discriminated union
 */
export const isValidRecordingStatus = (value: unknown): value is RecordingStatus => {
  if (typeof value !== 'object' || value === null) return false;

  const status = value as Record<string, unknown>;

  switch (status.type) {
    case 'idle':
      return Object.keys(status).length === 1;
    case 'initializing':
      return typeof status.message === 'string';
    case 'recording':
      return typeof status.startTime === 'number' && typeof status.duration === 'number';
    case 'paused':
      return typeof status.pausedAt === 'number' && typeof status.totalDuration === 'number';
    case 'completed':
      return (
        status.blob instanceof Blob &&
        typeof status.duration === 'number' &&
        typeof status.url === 'string'
      );
    case 'error':
      return typeof status.error === 'string';
    default:
      return false;
  }
};

/**
 * Validates if a value matches the UploadState discriminated union
 */
export const isValidUploadState = (value: unknown): value is UploadState => {
  if (typeof value !== 'object' || value === null) return false;

  const state = value as Record<string, unknown>;

  switch (state.status) {
    case 'idle':
      return Object.keys(state).length === 1;
    case 'preparing':
      return typeof state.message === 'string';
    case 'uploading':
      return (
        typeof state.progress === 'number' &&
        typeof state.bytesUploaded === 'number' &&
        typeof state.totalBytes === 'number' &&
        state.progress >= 0 &&
        state.progress <= 100
      );
    case 'processing':
      return typeof state.message === 'string';
    case 'success':
      return (
        typeof state.recording === 'object' &&
        state.recording !== null &&
        typeof state.uploadTime === 'number'
      );
    case 'error':
      return typeof state.error === 'string' && typeof state.retryable === 'boolean';
    default:
      return false;
  }
};

/**
 * Validates if a value matches the ScriptLoadingState discriminated union
 */
export const isValidScriptLoadingState = (value: unknown): value is ScriptLoadingState => {
  if (typeof value !== 'object' || value === null) return false;

  const state = value as Record<string, unknown>;

  switch (state.status) {
    case 'idle':
      return Object.keys(state).length === 1;
    case 'loading':
      return typeof state.duration === 'string';
    case 'loaded':
      return (
        typeof state.script === 'object' &&
        state.script !== null &&
        typeof state.loadTime === 'number'
      );
    case 'error':
      return typeof state.error === 'string' && typeof state.retryCount === 'number';
    default:
      return false;
  }
};

/**
 * Validates if a value is a valid StrictDurationOption
 */
export const isValidDurationOption = (value: unknown): value is StrictDurationOption => {
  if (typeof value !== 'object' || value === null) return false;

  const option = value as Record<string, unknown>;

  return (
    typeof option.value === 'string' &&
    ['2_minutes', '5_minutes', '10_minutes'].includes(option.value as string) &&
    typeof option.label === 'string' &&
    typeof option.minutes === 'number' &&
    [2, 5, 10].includes(option.minutes as number) &&
    typeof option.description === 'string' &&
    typeof option.maxFileSize === 'number' &&
    Array.isArray(option.recommendedFor) &&
    option.recommendedFor.every((item: unknown) => typeof item === 'string')
  );
};

// ============================================================================
// TYPE ASSERTION FUNCTIONS
// ============================================================================

/**
 * Asserts that a value is a valid RecordingStatus, throws if not
 */
export const assertRecordingStatus = (value: unknown): RecordingStatus => {
  if (!isValidRecordingStatus(value)) {
    throw new TypeError('Invalid RecordingStatus: ' + JSON.stringify(value));
  }
  return value;
};

/**
 * Asserts that a value is a valid UploadState, throws if not
 */
export const assertUploadState = (value: unknown): UploadState => {
  if (!isValidUploadState(value)) {
    throw new TypeError('Invalid UploadState: ' + JSON.stringify(value));
  }
  return value;
};

/**
 * Asserts that a value is a valid ScriptLoadingState, throws if not
 */
export const assertScriptLoadingState = (value: unknown): ScriptLoadingState => {
  if (!isValidScriptLoadingState(value)) {
    throw new TypeError('Invalid ScriptLoadingState: ' + JSON.stringify(value));
  }
  return value;
};

/**
 * Asserts that a value is a valid DurationOption, throws if not
 */
export const assertDurationOption = (value: unknown): StrictDurationOption => {
  if (!isValidDurationOption(value)) {
    throw new TypeError('Invalid DurationOption: ' + JSON.stringify(value));
  }
  return value;
};

// ============================================================================
// API RESPONSE VALIDATION
// ============================================================================

/**
 * Type guard for successful API responses
 */
export const isApiSuccess = <T>(response: unknown): response is StrictApiResponse<T> => {
  if (typeof response !== 'object' || response === null) return false;

  const res = response as Record<string, unknown>;

  return (
    res.success === true &&
    'data' in res &&
    typeof res.timestamp === 'string' &&
    typeof res.requestId === 'string'
  );
};

/**
 * Type guard for API error responses
 */
export const isApiError = (response: unknown): response is StrictApiError => {
  if (typeof response !== 'object' || response === null) return false;

  const res = response as Record<string, unknown>;

  return (
    res.success === false &&
    typeof res.error === 'object' &&
    res.error !== null &&
    typeof (res.error as Record<string, unknown>).message === 'string' &&
    typeof (res.error as Record<string, unknown>).code === 'string' &&
    typeof (res.error as Record<string, unknown>).statusCode === 'number' &&
    typeof res.timestamp === 'string' &&
    typeof res.requestId === 'string'
  );
};

/**
 * Validates and transforms raw API response to typed response
 */
export const validateApiResponse = <T>(
  response: unknown,
  dataValidator?: (data: unknown) => data is T
): StrictApiResponse<T> | StrictApiError => {
  if (isApiError(response)) {
    return response;
  }

  if (!isApiSuccess(response)) {
    throw new TypeError('Invalid API response format');
  }

  if (dataValidator && !dataValidator(response.data)) {
    throw new TypeError('Invalid API response data');
  }

  return response as StrictApiResponse<T>;
};

// ============================================================================
// NETWORK STATE UTILITIES
// ============================================================================

/**
 * Creates an idle network state
 */
export const createIdleNetworkState = <T>(): NetworkState<T> => ({
  status: 'idle',
});

/**
 * Creates a loading network state
 */
export const createLoadingNetworkState = <T>(signal?: AbortSignal): NetworkState<T> => {
  const state: NetworkState<T> = { status: 'loading' };
  if (signal) {
    (state as any).signal = signal;
  }
  return state;
};

/**
 * Creates a success network state
 */
export const createSuccessNetworkState = <T>(data: T): NetworkState<T> => ({
  status: 'success',
  data,
  timestamp: Date.now(),
});

/**
 * Creates an error network state
 */
export const createErrorNetworkState = <T>(error: string, statusCode?: number): NetworkState<T> => {
  const state: NetworkState<T> = { status: 'error', error };
  if (statusCode !== undefined) {
    (state as any).statusCode = statusCode;
  }
  return state;
};

/**
 * Type guard for network state status
 */
export const isNetworkState = <T>(
  state: NetworkState<T>,
  status: NetworkState<T>['status']
): boolean => {
  return state.status === status;
};

// ============================================================================
// TRANSFORMATION UTILITIES
// ============================================================================

/**
 * Transforms legacy recording state to new RecordingStatus
 */
export const transformLegacyRecordingState = (legacyState: {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  audioUrl: string | null;
}): RecordingStatus => {
  if (legacyState.audioBlob && legacyState.audioUrl) {
    return {
      type: 'completed',
      blob: legacyState.audioBlob,
      duration: legacyState.recordingTime,
      url: legacyState.audioUrl,
    };
  }

  if (legacyState.isRecording) {
    if (legacyState.isPaused) {
      return {
        type: 'paused',
        pausedAt: Date.now(),
        totalDuration: legacyState.recordingTime,
      };
    }
    return {
      type: 'recording',
      startTime: Date.now() - legacyState.recordingTime * 1000,
      duration: legacyState.recordingTime,
    };
  }

  return { type: 'idle' };
};

/**
 * Transforms legacy upload state to new UploadState
 */
export const transformLegacyUploadState = (legacyState: {
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress?: number;
  recording?: ValidatedVoiceRecording;
  error?: string;
}): UploadState => {
  switch (legacyState.status) {
    case 'idle':
      return { status: 'idle' };
    case 'uploading':
      return {
        status: 'uploading',
        progress: legacyState.progress || 0,
        bytesUploaded: 0,
        totalBytes: 100,
      };
    case 'success':
      return {
        status: 'success',
        recording: legacyState.recording!,
        uploadTime: Date.now(),
      };
    case 'error':
      return {
        status: 'error',
        error: legacyState.error || 'Unknown error',
        code: 'UPLOAD_ERROR',
        retryable: true,
      };
    default:
      return { status: 'idle' };
  }
};

// ============================================================================
// ERROR HANDLING UTILITIES
// ============================================================================

/**
 * Creates a standardized error object
 */
export const createStandardError = (
  message: string,
  code: string,
  statusCode?: number,
  details?: Record<string, unknown>
) => ({
  message,
  code,
  statusCode: statusCode || 500,
  details,
  timestamp: new Date().toISOString(),
});

/**
 * Extracts error message from various error types
 */
export const extractErrorMessage = (error: unknown): string => {
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message;
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    if (typeof err.message === 'string') return err.message;
    if (typeof err.error === 'string') return err.error;
  }
  return 'An unknown error occurred';
};

/**
 * Checks if an error is retryable based on its properties
 */
export const isRetryableError = (error: unknown): boolean => {
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;

    // Network errors are usually retryable
    if (err.type === 'network' || err.code === 'NETWORK_ERROR') return true;

    // Timeout errors are retryable
    if (err.type === 'timeout' || err.code === 'TIMEOUT') return true;

    // Server errors (5xx) are usually retryable
    if (typeof err.statusCode === 'number' && err.statusCode >= 500) return true;

    // Explicit retryable flag
    if (typeof err.retryable === 'boolean') return err.retryable;
  }

  return false;
};

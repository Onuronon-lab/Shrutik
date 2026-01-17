import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useScriptStore } from '../stores/scriptStore';
import { useSessionStore } from '../stores/sessionStore';
import { recordingService } from '../services/recording.service';
import { DurationOption } from '../types/state';
import { Script, RecordingSession } from '../types/api';

export interface UseScriptManagerReturn {
  // State
  currentScript: Script | null;
  selectedDuration: DurationOption | null;
  isLoading: boolean;
  error: string | null;
  recordingSession: RecordingSession | null;

  // Actions
  selectDuration: (duration: DurationOption) => Promise<void>;
  loadScript: (duration: DurationOption) => Promise<Script>;
  createSession: (scriptId: number) => Promise<RecordingSession>;
  clearError: () => void;
  reset: () => void;

  // Computed values
  isReady: boolean;
  canRecord: boolean;
}

export function useScriptManager(): UseScriptManagerReturn {
  const { t } = useTranslation();

  const {
    loadingState,
    selectedDuration,
    setLoadingState,
    setSelectedDuration,
    reset: resetScript,
  } = useScriptStore();

  const {
    current: recordingSession,
    setCurrent: setRecordingSession,
    setCreating,
    setError: setSessionError,
    reset: resetSession,
  } = useSessionStore();

  // Load script for selected duration
  const loadScript = useCallback(
    async (duration: DurationOption): Promise<Script> => {
      setLoadingState({ status: 'loading', duration: duration.value });

      try {
        // Check authentication
        const token = localStorage.getItem('auth_token');
        if (!token) {
          throw new Error('Please log in to access recording features');
        }

        const script = await recordingService.getRandomScript(duration.value);

        if (!script || typeof script !== 'object') {
          throw new Error('Invalid script data received');
        }

        setLoadingState({ status: 'loaded', script, loadTime: Date.now() });
        return script;
      } catch (err: any) {
        // Map technical errors to user-friendly translated messages
        let errorMessage: string;

        if (err.response?.status === 401) {
          errorMessage = 'Please log in to access recording features';
        } else if (err.response?.status === 404) {
          // No scripts available - use translated message
          errorMessage = t('error-no-scripts-available');
        } else if (err.response?.status === 500 || err.response?.status === 503) {
          // Server error - use translated message
          errorMessage = t('error-server-error');
        } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
          // Network error - use translated message
          errorMessage = t('error-network-error');
        } else if (err.response?.data?.detail) {
          // Use backend error if it's user-friendly
          errorMessage = err.response.data.detail;
        } else if (err.message) {
          // For other errors, use unknown error message
          errorMessage = t('error-unknown-error');
        } else {
          errorMessage = t('error-unknown-error');
        }

        setLoadingState({
          status: 'error',
          error: errorMessage,
          retryCount: 0,
        });
        throw new Error(errorMessage);
      }
    },
    [setLoadingState, t]
  );

  // Create recording session
  const createSession = useCallback(
    async (scriptId: number): Promise<RecordingSession> => {
      setCreating(true);
      setSessionError(null);

      try {
        const session = await recordingService.createRecordingSession(scriptId);

        if (!session || typeof session !== 'object') {
          throw new Error('Failed to create recording session');
        }

        setRecordingSession(session);
        return session;
      } catch (err: any) {
        // Map technical errors to user-friendly translated messages
        let errorMessage: string;

        if (err.response?.status === 500 || err.response?.status === 503) {
          errorMessage = t('error-server-error');
        } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
          errorMessage = t('error-network-error');
        } else if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        } else {
          errorMessage = t('error-unknown-error');
        }

        setSessionError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setCreating(false);
      }
    },
    [setCreating, setSessionError, setRecordingSession, t]
  );

  // Select duration and load script + create session
  const selectDuration = useCallback(
    async (duration: DurationOption) => {
      setSelectedDuration(duration);

      // Clear previous state
      setLoadingState({ status: 'idle' });
      setRecordingSession(null);
      setSessionError(null);

      try {
        // Load script first
        const script = await loadScript(duration);

        // Then create session
        await createSession(script.id);
      } catch (error) {
        // Error handling is done in individual functions
      }
    },
    [
      setSelectedDuration,
      setLoadingState,
      setRecordingSession,
      setSessionError,
      loadScript,
      createSession,
    ]
  );

  // Clear error
  const clearError = useCallback(() => {
    if (loadingState.status === 'error') {
      setLoadingState({ status: 'idle' });
    }
    setSessionError(null);
  }, [loadingState, setLoadingState, setSessionError]);

  // Reset all state
  const reset = useCallback(() => {
    resetScript();
    resetSession();
  }, [resetScript, resetSession]);

  // Computed values
  const currentScript = loadingState.status === 'loaded' ? loadingState.script : null;
  const isLoading = loadingState.status === 'loading';
  const error = loadingState.status === 'error' ? loadingState.error : null;
  const isReady = !!(currentScript && recordingSession && !isLoading);
  const canRecord = isReady && !error;

  return {
    // State
    currentScript,
    selectedDuration,
    isLoading,
    error: error || useSessionStore.getState().error,
    recordingSession,

    // Actions
    selectDuration,
    loadScript,
    createSession,
    clearError,
    reset,

    // Computed values
    isReady,
    canRecord,
  };
}

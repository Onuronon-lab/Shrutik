import { useCallback } from 'react';
import { useScriptStore } from '../stores/scriptStore';
import { useSessionStore } from '../stores/sessionStore';
import { recordingService } from '../services/recording.service';
import { DurationOption } from '../types/state';
import { Script, RecordingSession } from '../types/api';
import { useTranslation } from 'react-i18next';

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

  const { t } = useTranslation();

  // Load script for selected duration
  const loadScript = useCallback(
    async (duration: DurationOption): Promise<Script> => {
      setLoadingState({ status: 'loading', duration: duration.value });

      try {
        // Check authentication
        const token = localStorage.getItem('auth_token');
        if (!token) {
          throw new Error(t('login-record-error'));
        }

        const script = await recordingService.getRandomScript(duration.value);

        if (!script || typeof script !== 'object') {
          throw new Error(t('invalid-script'));
        }

        setLoadingState({ status: 'loaded', script, loadTime: Date.now() });
        return script;
      } catch (err: any) {
        console.error(t('script-load-error'), err);

        let errorMessage = t('script-load-fail');
        if (err.response?.status === 401) {
          errorMessage = t('login-record-error');
        } else if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.message) {
          errorMessage = err.message;
        }

        setLoadingState({
          status: 'error',
          error: typeof errorMessage === 'string' ? errorMessage : t('script-load-fail'),
          retryCount: 0,
        });
        throw new Error(errorMessage);
      }
    },
    [setLoadingState]
  );

  // Create recording session
  const createSession = useCallback(
    async (scriptId: number): Promise<RecordingSession> => {
      setCreating(true);
      setSessionError(null);

      try {
        const session = await recordingService.createRecordingSession(scriptId);

        if (!session || typeof session !== 'object') {
          throw new Error(t('record-session-create-fail'));
        }

        setRecordingSession(session);
        return session;
      } catch (err: any) {
        console.error(t('session-error'), err);

        let errorMessage = t('record-session-create-fail');
        if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.message) {
          errorMessage = err.message;
        }

        setSessionError(
          typeof errorMessage === 'string' ? errorMessage : t('record-session-create-fail')
        );
        throw new Error(errorMessage);
      } finally {
        setCreating(false);
      }
    },
    [setCreating, setSessionError, setRecordingSession]
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
        console.error('Error in selectDuration:', error);
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

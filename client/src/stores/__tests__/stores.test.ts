import { describe, it, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { useRecordingStore } from '../recordingStore';
import { useScriptStore } from '../scriptStore';
import { useUploadStore } from '../uploadStore';
import { useSessionStore } from '../sessionStore';
import { useAppStore } from '../appStore';
import { RecordingStatus } from '../../types/state';

describe('Zustand Stores', () => {
  beforeEach(() => {
    // Reset all stores before each test
    useRecordingStore.getState().reset();
    useScriptStore.getState().reset();
    useUploadStore.getState().reset();
    useSessionStore.getState().reset();
  });

  describe('RecordingStore', () => {
    it('should initialize with idle state', () => {
      const state = useRecordingStore.getState();
      expect(state.status.type).toBe('idle');
      expect(state.recordingTime).toBe(0);
      expect(state.audioBlob).toBeNull();
      expect(state.audioUrl).toBeNull();
    });

    it('should update recording time', () => {
      const { setRecordingTime } = useRecordingStore.getState();
      setRecordingTime(30);

      const state = useRecordingStore.getState();
      expect(state.recordingTime).toBe(30);
    });

    it('should increment recording time', () => {
      const { incrementRecordingTime } = useRecordingStore.getState();
      incrementRecordingTime();
      incrementRecordingTime();

      const state = useRecordingStore.getState();
      expect(state.recordingTime).toBe(2);
    });

    it('should set recording status', () => {
      const { setStatus } = useRecordingStore.getState();
      setStatus({ type: 'recording', startTime: Date.now() });

      const state = useRecordingStore.getState();
      expect(state.status.type).toBe('recording');
    });
  });

  describe('ScriptStore', () => {
    it('should initialize with idle loading state', () => {
      const state = useScriptStore.getState();
      expect(state.loadingState.status).toBe('idle');
      expect(state.selectedDuration).toBeNull();
    });

    it('should set loading state', () => {
      const { setLoadingState } = useScriptStore.getState();
      setLoadingState({ status: 'loading', duration: '5_minutes' });

      const state = useScriptStore.getState();
      expect(state.loadingState.status).toBe('loading');
      if (state.loadingState.status === 'loading') {
        expect(state.loadingState.duration).toBe('5_minutes');
      }
    });

    it('should set error state', () => {
      const { setLoadingState } = useScriptStore.getState();
      setLoadingState({ status: 'error', error: 'Test error', retryCount: 0 });

      const state = useScriptStore.getState();
      expect(state.loadingState.status).toBe('error');
      if (state.loadingState.status === 'error') {
        expect(state.loadingState.error).toBe('Test error');
      }
    });
  });

  describe('UploadStore', () => {
    it('should initialize with idle state', () => {
      const state = useUploadStore.getState();
      expect(state.state.status).toBe('idle');
    });

    it('should set uploading state with progress', () => {
      const { setUploading } = useUploadStore.getState();
      setUploading(50);

      const state = useUploadStore.getState();
      expect(state.state.status).toBe('uploading');
      if (state.state.status === 'uploading') {
        expect(state.state.progress).toBe(50);
      }
    });

    it('should update progress when uploading', () => {
      const { setUploading, updateProgress } = useUploadStore.getState();
      setUploading(25);
      updateProgress(75);

      const state = useUploadStore.getState();
      if (state.state.status === 'uploading') {
        expect(state.state.progress).toBe(75);
      }
    });

    it('should set error state', () => {
      const { setError } = useUploadStore.getState();
      setError('Upload failed');

      const state = useUploadStore.getState();
      expect(state.state.status).toBe('error');
      if (state.state.status === 'error') {
        expect(state.state.error).toBe('Upload failed');
      }
    });
  });

  describe('SessionStore', () => {
    it('should initialize with null session', () => {
      const state = useSessionStore.getState();
      expect(state.current).toBeNull();
      expect(state.isCreating).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should set creating state', () => {
      const { setCreating } = useSessionStore.getState();
      setCreating(true);

      const state = useSessionStore.getState();
      expect(state.isCreating).toBe(true);
    });
  });

  describe('AppStore', () => {
    it('should reset all stores', () => {
      // Set some state in different stores
      useRecordingStore.getState().setRecordingTime(30);
      useScriptStore.getState().setLoadingState({ status: 'loading', duration: '5_minutes' });
      useUploadStore.getState().setUploading(50);
      useSessionStore.getState().setCreating(true);

      // Reset all
      useAppStore.getState().resetAll();

      // Verify all stores are reset
      expect(useRecordingStore.getState().recordingTime).toBe(0);
      expect(useScriptStore.getState().loadingState.status).toBe('idle');
      expect(useUploadStore.getState().state.status).toBe('idle');
      expect(useSessionStore.getState().isCreating).toBe(false);
    });

    it('should start new recording session', () => {
      // Set some recording and upload state
      useRecordingStore.getState().setRecordingTime(30);
      useUploadStore.getState().setUploading(50);

      // Start new session
      useAppStore.getState().startNewRecordingSession();

      // Verify recording and upload are reset
      expect(useRecordingStore.getState().recordingTime).toBe(0);
      expect(useUploadStore.getState().state.status).toBe('idle');
    });
  });

  describe('Property-Based Tests', () => {
    /**
     * **Feature: frontend-modernization, Property 2: State consistency across components**
     * **Validates: Requirements 2.1, 2.2, 2.4**
     */
    it('should maintain state consistency across all store subscriptions', () => {
      fc.assert(
        fc.property(
          // Generate arbitrary state changes for different stores
          fc.record({
            recordingTime: fc.integer({ min: 0, max: 3600 }),
            recordingStatus: fc.oneof(
              fc.constant({ type: 'idle' as const }),
              fc.record({
                type: fc.constant('recording' as const),
                startTime: fc.integer({ min: 0, max: Date.now() }),
                duration: fc.integer({ min: 0, max: 3600 }),
              }),
              fc.record({
                type: fc.constant('paused' as const),
                pausedAt: fc.integer({ min: 0, max: Date.now() }),
                totalDuration: fc.integer({ min: 0, max: 3600 }),
              })
            ),
            scriptLoadingState: fc.oneof(
              fc.constant({ status: 'idle' as const }),
              fc.record({
                status: fc.constant('loading' as const),
                duration: fc.constantFrom('2_minutes', '5_minutes', '10_minutes'),
              }),
              fc.record({
                status: fc.constant('error' as const),
                error: fc.string(),
                retryCount: fc.integer({ min: 0, max: 3 }),
              })
            ),
            uploadProgress: fc.integer({ min: 0, max: 100 }),
            uploadError: fc.option(fc.string(), { nil: null }),
            sessionCreating: fc.boolean(),
            sessionError: fc.option(fc.string(), { nil: null }),
          }),
          stateChanges => {
            // Reset all stores to initial state
            useAppStore.getState().resetAll();

            // Apply state changes to different stores
            useRecordingStore.getState().setRecordingTime(stateChanges.recordingTime);
            useRecordingStore.getState().setStatus(stateChanges.recordingStatus as RecordingStatus);
            useScriptStore.getState().setLoadingState(stateChanges.scriptLoadingState);

            if (stateChanges.uploadError) {
              useUploadStore.getState().setError(stateChanges.uploadError);
            } else {
              useUploadStore.getState().setUploading(stateChanges.uploadProgress);
            }

            useSessionStore.getState().setCreating(stateChanges.sessionCreating);
            useSessionStore.getState().setError(stateChanges.sessionError);

            // Verify that all stores reflect the applied changes consistently
            const recordingState = useRecordingStore.getState();
            const scriptState = useScriptStore.getState();
            const uploadState = useUploadStore.getState();
            const sessionState = useSessionStore.getState();

            // State consistency checks - each store should reflect exactly what was set
            expect(recordingState.recordingTime).toBe(stateChanges.recordingTime);
            expect(recordingState.status).toEqual(stateChanges.recordingStatus);
            expect(scriptState.loadingState).toEqual(stateChanges.scriptLoadingState);
            expect(sessionState.isCreating).toBe(stateChanges.sessionCreating);
            expect(sessionState.error).toBe(stateChanges.sessionError);

            // Upload state consistency check
            if (stateChanges.uploadError) {
              expect(uploadState.state.status).toBe('error');
              if (uploadState.state.status === 'error') {
                expect(uploadState.state.error).toBe(stateChanges.uploadError);
              }
            } else {
              expect(uploadState.state.status).toBe('uploading');
              if (uploadState.state.status === 'uploading') {
                expect(uploadState.state.progress).toBe(stateChanges.uploadProgress);
              }
            }

            // Verify that multiple subscriptions to the same store return identical state
            const recordingState2 = useRecordingStore.getState();
            const scriptState2 = useScriptStore.getState();
            const uploadState2 = useUploadStore.getState();
            const sessionState2 = useSessionStore.getState();

            expect(recordingState).toEqual(recordingState2);
            expect(scriptState).toEqual(scriptState2);
            expect(uploadState).toEqual(uploadState2);
            expect(sessionState).toEqual(sessionState2);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

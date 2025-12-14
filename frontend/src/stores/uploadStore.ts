import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { UploadState } from '../types/state';
import { VoiceRecording } from '../types/api';

interface UploadStore {
  state: UploadState;
  // Actions
  setIdle: () => void;
  setUploading: (progress: number) => void;
  setSuccess: (recording: VoiceRecording) => void;
  setError: (error: string) => void;
  updateProgress: (progress: number) => void;
  reset: () => void;
}

const initialState: UploadState = { status: 'idle' };

export const useUploadStore = create<UploadStore>()(
  devtools(
    set => ({
      state: initialState,

      setIdle: () => set({ state: { status: 'idle' } }, false, 'setIdle'),

      setUploading: progress =>
        set(
          { state: { status: 'uploading', progress, bytesUploaded: 0, totalBytes: 0 } },
          false,
          'setUploading'
        ),

      setSuccess: recording =>
        set(
          { state: { status: 'success', recording, uploadTime: Date.now() } },
          false,
          'setSuccess'
        ),

      setError: error =>
        set({ state: { status: 'error', error, retryable: true } }, false, 'setError'),

      updateProgress: progress =>
        set(
          state =>
            state.state.status === 'uploading' ? { state: { ...state.state, progress } } : state,
          false,
          'updateProgress'
        ),

      reset: () => set({ state: initialState }, false, 'reset'),
    }),
    {
      name: 'upload-store',
    }
  )
);

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { RecordingState, RecordingStatus } from '../types/state';

interface RecordingStore extends RecordingState {
  // Actions
  setStatus: (status: RecordingStatus) => void;
  setRecordingTime: (time: number) => void;
  incrementRecordingTime: () => void;
  setAudioBlob: (blob: Blob | null) => void;
  setAudioUrl: (url: string | null) => void;
  setMediaRecorder: (recorder: MediaRecorder | null) => void;
  setStream: (stream: MediaStream | null) => void;
  reset: () => void;
  cleanup: () => void;
}

const initialState: RecordingState = {
  status: { type: 'idle' },
  recordingTime: 0,
  audioBlob: null,
  audioUrl: null,
  mediaRecorder: null,
  stream: null,
  error: null,
};

export const useRecordingStore = create<RecordingStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setStatus: status => set({ status }, false, 'setStatus'),

      setRecordingTime: recordingTime => set({ recordingTime }, false, 'setRecordingTime'),

      incrementRecordingTime: () =>
        set(state => ({ recordingTime: state.recordingTime + 1 }), false, 'incrementRecordingTime'),

      setAudioBlob: audioBlob => set({ audioBlob }, false, 'setAudioBlob'),

      setAudioUrl: audioUrl => {
        const currentUrl = get().audioUrl;
        if (currentUrl && currentUrl !== audioUrl) {
          URL.revokeObjectURL(currentUrl);
        }
        set({ audioUrl }, false, 'setAudioUrl');
      },

      setMediaRecorder: mediaRecorder => set({ mediaRecorder }, false, 'setMediaRecorder'),

      setStream: stream => {
        const currentStream = get().stream;
        if (currentStream && currentStream !== stream) {
          currentStream.getTracks().forEach(track => track.stop());
        }
        set({ stream }, false, 'setStream');
      },

      reset: () => {
        const { audioUrl, stream } = get();

        // Cleanup resources
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl);
        }
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }

        set(initialState, false, 'reset');
      },

      cleanup: () => {
        const { audioUrl, stream } = get();

        if (audioUrl) {
          URL.revokeObjectURL(audioUrl);
        }
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }
      },
    }),
    {
      name: 'recording-store',
    }
  )
);

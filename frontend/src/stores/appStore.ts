import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { useRecordingStore } from './recordingStore';
import { useScriptStore } from './scriptStore';
import { useUploadStore } from './uploadStore';
import { useSessionStore } from './sessionStore';

// Combined store for complex operations that need to coordinate between multiple stores
interface AppStore {
  // Global actions that coordinate between stores
  resetAll: () => void;
  startNewRecordingSession: () => void;
}

export const useAppStore = create<AppStore>()(
  devtools(
    () => ({
      resetAll: () => {
        useRecordingStore.getState().reset();
        useScriptStore.getState().reset();
        useUploadStore.getState().reset();
        useSessionStore.getState().reset();
      },

      startNewRecordingSession: () => {
        // Reset recording and upload states for a fresh start
        useRecordingStore.getState().reset();
        useUploadStore.getState().reset();
        // Keep script and session states as they might be reused
      },
    }),
    {
      name: 'app-store',
    }
  )
);

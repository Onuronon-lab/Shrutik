// Central exports for all Zustand stores
export { useRecordingStore } from './recordingStore';
export { useScriptStore } from './scriptStore';
export { useUploadStore } from './uploadStore';
export { useSessionStore } from './sessionStore';
export { useAppStore } from './appStore';

// Re-export types for convenience
export type {
  RecordingState,
  RecordingStatus,
  ScriptState,
  SessionState,
  UploadState,
  DurationOption,
  AppState,
} from '../types/state';

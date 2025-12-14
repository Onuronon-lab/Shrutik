// Export all custom hooks
export { useAsync } from './useAsync';
export { useAsyncResource } from './useAsyncResource';
export { useErrorHandler } from './useErrorHandler';
export { useModal } from './useModal';
export { useTheme } from './useTheme';

// New custom hooks for frontend modernization
export { useAudioRecorder } from './useAudioRecorder';
export { useScriptManager } from './useScriptManager';
export { useUploadManager } from './useUploadManager';
export { useDurationSelector } from './useDurationSelector';

// Re-export types for convenience
export type { UseAudioRecorderReturn } from './useAudioRecorder';
export type { UseScriptManagerReturn } from './useScriptManager';
export type { UseUploadManagerReturn, UploadMetadata } from './useUploadManager';
export type { UseDurationSelectorReturn } from './useDurationSelector';

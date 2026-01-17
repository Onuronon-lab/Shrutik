import { useCallback } from 'react';
import { useUploadStore } from '../stores/uploadStore';
import { recordingService } from '../services/recording.service';
import { VoiceRecording } from '../types/api';
import { UploadState } from '../types/state';

export interface UploadMetadata {
  session_id: string;
  duration: number;
  audio_format: string;
  file_size: number;
  sample_rate?: number;
  channels?: number;
  bit_depth?: number;
}

export interface UseUploadManagerReturn {
  // State
  uploadState: UploadState;

  // Actions
  uploadRecording: (audioBlob: Blob, metadata: UploadMetadata) => Promise<VoiceRecording>;
  retryUpload: () => Promise<VoiceRecording | null>;
  reset: () => void;

  // Computed values
  isUploading: boolean;
  isSuccess: boolean;
  isError: boolean;
  isIdle: boolean;
  progress: number;
  errorMessage: string | null;
  uploadedRecording: VoiceRecording | null;
}

export function useUploadManager(): UseUploadManagerReturn {
  const {
    state: uploadState,

    setUploading,
    setSuccess,
    setError,
    updateProgress,
    reset,
  } = useUploadStore();

  // Store last upload parameters for retry functionality
  let lastUploadParams: { blob: Blob; metadata: UploadMetadata } | null = null;

  // Create audio file with metadata
  const createAudioFile = useCallback((blob: Blob): File => {
    return new File([blob], 'recording.webm', { type: 'audio/webm' });
  }, []);

  // Upload recording with progress tracking
  const uploadRecording = useCallback(
    async (audioBlob: Blob, metadata: UploadMetadata): Promise<VoiceRecording> => {
      // Store for potential retry
      lastUploadParams = { blob: audioBlob, metadata };

      setUploading(0);

      try {
        const audioFile = createAudioFile(audioBlob);

        // Prepare upload data
        const uploadData = {
          session_id: metadata.session_id,
          duration: metadata.duration,
          audio_format: metadata.audio_format,
          file_size: metadata.file_size,
          sample_rate: metadata.sample_rate || 48000,
          channels: metadata.channels || 1,
          bit_depth: metadata.bit_depth || 16,
        };

        // Simulate progress updates (since we don't have real progress from the API)
        const progressInterval = setInterval(() => {
          const currentState = useUploadStore.getState().state;
          if (currentState.status === 'uploading') {
            const newProgress = Math.min(currentState.progress + 10, 90);
            updateProgress(newProgress);
          }
        }, 200);

        try {
          const recording = await recordingService.uploadRecording(audioFile, uploadData);

          clearInterval(progressInterval);
          setSuccess(recording);

          return recording;
        } catch (sessionError: any) {
          clearInterval(progressInterval);

          // Handle session-related errors by attempting to create a new session
          if (
            (sessionError.response?.status === 400 &&
              sessionError.response?.data?.detail?.includes('session')) ||
            sessionError.response?.status === 403
          ) {
            // This would require access to script manager to create a new session
            // For now, we'll just throw the error and let the caller handle it
            throw new Error('Session expired. Please try recording again.');
          }

          // Re-throw other errors
          throw sessionError;
        }
      } catch (err: any) {
        let errorMessage = 'Failed to upload recording';
        if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.message) {
          errorMessage = err.message;
        }

        setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to upload recording');
        throw new Error(errorMessage);
      }
    },
    [createAudioFile, setUploading, setSuccess, setError, updateProgress]
  );

  // Retry last upload
  const retryUpload = useCallback(async (): Promise<VoiceRecording | null> => {
    if (!lastUploadParams) {
      return null;
    }

    return uploadRecording(lastUploadParams.blob, lastUploadParams.metadata);
  }, [uploadRecording]);

  // Computed values
  const isUploading = uploadState.status === 'uploading';
  const isSuccess = uploadState.status === 'success';
  const isError = uploadState.status === 'error';
  const isIdle = uploadState.status === 'idle';

  const progress = uploadState.status === 'uploading' ? uploadState.progress : 0;
  const errorMessage = uploadState.status === 'error' ? uploadState.error : null;
  const uploadedRecording = uploadState.status === 'success' ? uploadState.recording : null;

  return {
    // State
    uploadState,

    // Actions
    uploadRecording,
    retryUpload,
    reset,

    // Computed values
    isUploading,
    isSuccess,
    isError,
    isIdle,
    progress,
    errorMessage,
    uploadedRecording,
  };
}

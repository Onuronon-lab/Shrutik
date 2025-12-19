import { useCallback, useRef, useEffect } from 'react';
import { useRecordingStore } from '../stores/recordingStore';
import { RecordingStatus } from '../types/state';
import { useTranslation } from 'react-i18next';

export interface UseAudioRecorderReturn {
  // State
  status: RecordingStatus;
  recordingTime: number;
  audioBlob: Blob | null;
  audioUrl: string | null;

  // Actions
  startRecording: (maxDuration?: number) => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  resetRecording: () => void;
  playRecording: () => void;

  // Computed values
  isRecording: boolean;
  isPaused: boolean;
  isCompleted: boolean;
  progressPercentage: (maxDuration: number) => number;
  remainingTime: (maxDuration: number) => number;
  formattedTime: string;
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const {
    status,
    recordingTime,
    audioBlob,
    audioUrl,
    mediaRecorder,

    setStatus,
    setRecordingTime,
    incrementRecordingTime,
    setAudioBlob,
    setAudioUrl,
    setMediaRecorder,
    setStream,
    reset,
    cleanup,
  } = useRecordingStore();

  // Refs for managing recording
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const maxDurationRef = useRef<number>(600); // Default 10 minutes
  const { t } = useTranslation();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [cleanup]);

  // Start recording
  const startRecording = useCallback(
    async (maxDuration = 600) => {
      try {
        maxDurationRef.current = maxDuration;

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100,
          },
        });

        setStream(stream);
        chunksRef.current = [];

        const recorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus',
        });

        setMediaRecorder(recorder);

        recorder.ondataavailable = event => {
          if (event.data.size > 0) {
            chunksRef.current.push(event.data);
          }
        };

        recorder.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          const url = URL.createObjectURL(blob);

          setAudioBlob(blob);
          setAudioUrl(url);
          setStatus({ type: 'completed', blob, duration: recordingTime, url });

          // Clear timer
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
        };

        recorder.start(1000);
        setStatus({ type: 'recording', startTime: Date.now(), duration: 0 });
        setRecordingTime(0);

        // Start timer
        timerRef.current = setInterval(() => {
          incrementRecordingTime();

          // Auto-stop when max duration reached
          const currentTime = useRecordingStore.getState().recordingTime + 1;
          if (currentTime >= maxDuration) {
            if (recorder.state === 'recording') {
              recorder.stop();
            }
          }
        }, 1000);
      } catch (error) {
        console.error(t('recording_start_error'), error);
        throw new Error(t('mic_permission_failed'));
      }
    },
    [
      setStream,
      setMediaRecorder,
      setAudioBlob,
      setAudioUrl,
      setStatus,
      setRecordingTime,
      incrementRecordingTime,
    ]
  );

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorder && status.type === 'recording') {
      mediaRecorder.stop();

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [mediaRecorder, status]);

  // Pause recording
  const pauseRecording = useCallback(() => {
    if (mediaRecorder && status.type === 'recording') {
      mediaRecorder.pause();
      setStatus({ type: 'paused', pausedAt: Date.now(), totalDuration: recordingTime });

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [mediaRecorder, status, setStatus]);

  // Resume recording
  const resumeRecording = useCallback(() => {
    if (mediaRecorder && status.type === 'paused') {
      mediaRecorder.resume();
      setStatus({ type: 'recording', startTime: Date.now(), duration: recordingTime });

      // Restart timer
      timerRef.current = setInterval(() => {
        incrementRecordingTime();

        // Auto-stop when max duration reached
        const currentTime = useRecordingStore.getState().recordingTime + 1;
        if (currentTime >= maxDurationRef.current) {
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
        }
      }, 1000);
    }
  }, [mediaRecorder, status, setStatus, incrementRecordingTime]);

  // Reset recording
  const resetRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    reset();
  }, [reset]);

  // Play recorded audio
  const playRecording = useCallback(() => {
    if (audioUrl) {
      if (!audioRef.current) {
        audioRef.current = new Audio(audioUrl);
      } else {
        audioRef.current.src = audioUrl;
      }
      audioRef.current.play().catch(console.error);
    }
  }, [audioUrl]);

  // Computed values
  const isRecording = status.type === 'recording';
  const isPaused = status.type === 'paused';
  const isCompleted = status.type === 'completed';

  const progressPercentage = useCallback(
    (maxDuration: number) => {
      return (recordingTime / maxDuration) * 100;
    },
    [recordingTime]
  );

  const remainingTime = useCallback(
    (maxDuration: number) => {
      return Math.max(0, maxDuration - recordingTime);
    },
    [recordingTime]
  );

  const formattedTime = (() => {
    const mins = Math.floor(recordingTime / 60);
    const secs = recordingTime % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  })();

  return {
    // State
    status,
    recordingTime,
    audioBlob,
    audioUrl,

    // Actions
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
    playRecording,

    // Computed values
    isRecording,
    isPaused,
    isCompleted,
    progressPercentage,
    remainingTime,
    formattedTime,
  };
}

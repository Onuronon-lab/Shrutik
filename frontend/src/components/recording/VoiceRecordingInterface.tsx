import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  MicrophoneIcon,
  StopIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/solid';
import { ClockIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import { Script, RecordingSession, VoiceRecording } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';
import AudioVisualizer from './AudioVisualizer';
import { useTranslation } from 'react-i18next';

type DurationOption = {
  value: '2_minutes' | '5_minutes' | '10_minutes';
  label: string;
  minutes: number;
  description: string;
};

interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  audioUrl: string | null;
}

interface VoiceRecordingInterfaceProps {
  onRecordingComplete?: (recording: VoiceRecording) => void;
}

const VoiceRecordingInterface: React.FC<VoiceRecordingInterfaceProps> = ({
  onRecordingComplete,
}) => {
  const { t } = useTranslation();

  const DURATION_OPTIONS: DurationOption[] = [
    {
      value: '2_minutes',
      label: t('recordPage-2-minutes'),
      minutes: 2,
      description: t('recordPage-quick-record-session'),
    },
    {
      value: '5_minutes',
      label: t('recordPage-5-minutes'),
      minutes: 5,
      description: t('recordPage-standard-record-session'),
    },
    {
      value: '10_minutes',
      label: t('recordPage-10-minutes'),
      minutes: 10,
      description: t('recordPage-extended-record-session'),
    },
  ];
  // State management
  const [selectedDuration, setSelectedDuration] = useState<DurationOption | null>(null);
  const [currentScript, setCurrentScript] = useState<Script | null>(null);
  const [recordingSession, setRecordingSession] = useState<RecordingSession | null>(null);
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    recordingTime: 0,
    audioBlob: null,
    audioUrl: null,
  });
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>(
    'idle'
  );

  // Refs for audio recording
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (recordingState.audioUrl) {
      URL.revokeObjectURL(recordingState.audioUrl);
    }
  }, [recordingState.audioUrl]);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  // Load script when duration is selected
  const loadScript = useCallback(async (duration: DurationOption) => {
    setIsLoading(true);
    setError(null);

    try {
      // Check if user is authenticated
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError('Please log in to access recording features');
        return;
      }

      const script = await apiService.getRandomScript(duration.value);
      if (!script || typeof script !== 'object') {
        setError('Invalid script data received');
        return;
      }

      setCurrentScript(script);

      // Create recording session
      const session = await apiService.createRecordingSession(script.id);
      if (!session || typeof session !== 'object') {
        setError('Failed to create recording session');
        return;
      }

      setRecordingSession(session);
    } catch (err: any) {
      console.error('Load script error:', err);
      let errorMessage = 'Failed to load script';

      if (err.response?.status === 401) {
        errorMessage = 'Please log in to access recording features';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to load script');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle duration selection
  const handleDurationSelect = useCallback(
    (duration: DurationOption) => {
      setSelectedDuration(duration);
      setCurrentScript(null);
      setRecordingSession(null);
      setRecordingState(prev => ({ ...prev, audioBlob: null, audioUrl: null }));
      setUploadStatus('idle');
      loadScript(duration);
    },
    [loadScript]
  );

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        },
      });

      streamRef.current = stream;
      chunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = event => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);

        setRecordingState(prev => ({
          ...prev,
          audioBlob,
          audioUrl,
          isRecording: false,
          isPaused: false,
        }));

        cleanup();
      };

      mediaRecorder.start(1000);
      setRecordingState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        recordingTime: 0,
      }));

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingState(prev => {
          const newTime = prev.recordingTime + 1;
          const maxTime = (selectedDuration?.minutes || 10) * 60;

          if (newTime >= maxTime) {
            // Call stopRecording directly to avoid dependency issues
            if (mediaRecorderRef.current && prev.isRecording) {
              mediaRecorderRef.current.stop();

              if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
              }
            }
          }

          return { ...prev, recordingTime: newTime };
        });
      }, 1000);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to access microphone. Please check permissions.');
    }
  }, [selectedDuration, cleanup]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState.isRecording) {
      mediaRecorderRef.current.stop();

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [recordingState.isRecording]);

  // Pause/Resume recording
  const togglePauseRecording = useCallback(() => {
    if (!mediaRecorderRef.current) return;

    if (recordingState.isPaused) {
      mediaRecorderRef.current.resume();
      // Resume timer
      timerRef.current = setInterval(() => {
        setRecordingState(prev => {
          const newTime = prev.recordingTime + 1;
          const maxTime = (selectedDuration?.minutes || 10) * 60;

          if (newTime >= maxTime) {
            // Call stopRecording directly to avoid dependency issues
            if (mediaRecorderRef.current && prev.isRecording) {
              mediaRecorderRef.current.stop();

              if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
              }
            }
          }

          return { ...prev, recordingTime: newTime };
        });
      }, 1000);
    } else {
      mediaRecorderRef.current.pause();
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    setRecordingState(prev => ({ ...prev, isPaused: !prev.isPaused }));
  }, [recordingState.isPaused, selectedDuration]);

  // Upload recording
  const uploadRecording = useCallback(async () => {
    if (!recordingState.audioBlob || !recordingSession || !currentScript) {
      setError('No recording, session, or script available');
      return;
    }

    setUploadStatus('uploading');
    setUploadProgress(0);
    setError(null);

    try {
      // Convert webm to wav for better compatibility
      const audioFile = new File([recordingState.audioBlob], 'recording.webm', {
        type: 'audio/webm',
      });

      let sessionToUse = recordingSession;

      // Try to upload with current session first
      let uploadData = {
        session_id: sessionToUse.session_id,
        duration: recordingState.recordingTime,
        audio_format: 'webm',
        file_size: recordingState.audioBlob.size,
        sample_rate: 44100,
        channels: 1,
        bit_depth: 16,
      };

      console.log('Upload data:', uploadData);
      console.log('Audio file:', audioFile);

      try {
        const recording = await apiService.uploadRecording(audioFile, uploadData);

        setUploadStatus('success');
        setUploadProgress(100);

        if (onRecordingComplete) {
          onRecordingComplete(recording);
        }
        return;
      } catch (sessionError: any) {
        // If session is invalid or forbidden, try to create a new one
        if (
          (sessionError.response?.status === 400 &&
            sessionError.response?.data?.detail?.includes('session')) ||
          sessionError.response?.status === 403
        ) {
          console.log('Session expired, creating new session...');

          // Create new session
          const newSession = await apiService.createRecordingSession(currentScript.id);
          setRecordingSession(newSession);

          // Small delay to ensure session is stored
          await new Promise(resolve => setTimeout(resolve, 100));

          // Update upload data with new session
          uploadData.session_id = newSession.session_id;

          // Retry upload with new session
          const recording = await apiService.uploadRecording(audioFile, uploadData);

          setUploadStatus('success');
          setUploadProgress(100);

          if (onRecordingComplete) {
            onRecordingComplete(recording);
          }
          return;
        }

        // If it's not a session error, re-throw
        throw sessionError;
      }
    } catch (err: any) {
      console.error('Upload error:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to upload recording';
      setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to upload recording');
      setUploadStatus('error');
    }
  }, [
    recordingState.audioBlob,
    recordingState.recordingTime,
    recordingSession,
    currentScript,
    onRecordingComplete,
  ]);

  // Play recorded audio
  const playRecording = useCallback(() => {
    if (recordingState.audioUrl && audioRef.current) {
      audioRef.current.play();
    }
  }, [recordingState.audioUrl]);

  // Reset to start over
  const resetRecording = useCallback(() => {
    setRecordingState({
      isRecording: false,
      isPaused: false,
      recordingTime: 0,
      audioBlob: null,
      audioUrl: null,
    });
    setUploadStatus('idle');
    setUploadProgress(0);
    setError(null);

    if (selectedDuration) {
      loadScript(selectedDuration);
    }
  }, [selectedDuration, loadScript]);

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get progress percentage
  const getProgressPercentage = () => {
    if (!selectedDuration) return 0;
    const maxTime = selectedDuration.minutes * 60;
    return (recordingState.recordingTime / maxTime) * 100;
  };

  // Get remaining time
  const getRemainingTime = () => {
    if (!selectedDuration) return 0;
    const maxTime = selectedDuration.minutes * 60;
    return Math.max(0, maxTime - recordingState.recordingTime);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Duration Selection */}
      {!selectedDuration && (
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center">
            <ClockIcon className="w-5 h-5 mr-2" />
            {t('recordPage-selection-record-duration')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {DURATION_OPTIONS.map(option => (
              <button
                key={option.value}
                onClick={() => handleDurationSelect(option)}
                className="p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-nutral transition-all duration-200 text-left"
              >
                <div className="font-semibold text-foreground">{option.label}</div>
                <div className="text-sm text-secondary-foreground mt-1">{option.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Script Display */}
      {selectedDuration && (
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground flex items-center">
              <DocumentTextIcon className="w-5 h-5 mr-2" />
              Script ({selectedDuration.label})
            </h2>
            <button
              onClick={() => setSelectedDuration(null)}
              className="text-sm text-primary hover:text-primary-hover"
            >
              Change Duration
            </button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="md" />
              <span className="ml-2 text-secondary-foreground">Loading script...</span>
            </div>
          ) : currentScript ? (
            <div className="bg-nutral rounded-lg p-4 mb-4">
              <div className="text-lg leading-relaxed text-foreground font-bengali">
                {currentScript.text}
              </div>
            </div>
          ) : error ? (
            <div className="bg-destructive border border-distructive-border rounded-lg p-4 mb-4">
              <div className="flex items-center text-destructive-foreground">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                {error}
              </div>
              <button
                onClick={() => selectedDuration && loadScript(selectedDuration)}
                className="mt-2 text-sm text-destructive-foreground hover:text-destructive-foreground hover:underline"
              >
                Try Again
              </button>
            </div>
          ) : null}
        </div>
      )}

      {/* Recording Controls */}
      {currentScript && recordingSession && (
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">{t('record-control')}</h3>

          {/* Recording Status */}
          <div className="text-center mb-6">
            <div className="text-3xl font-mono font-bold text-foreground mb-2">
              {formatTime(recordingState.recordingTime)}
            </div>
            <div className="text-sm text-secondary-foreground mb-4">
              {recordingState.isRecording
                ? recordingState.isPaused
                  ? 'Paused'
                  : 'Recording...'
                : recordingState.audioBlob
                  ? 'Recording Complete'
                  : 'Ready to Record'}
            </div>

            {/* Audio Visualizer */}
            {recordingState.isRecording && (
              <div className="mb-4">
                <AudioVisualizer
                  isRecording={recordingState.isRecording && !recordingState.isPaused}
                  stream={streamRef.current}
                  className="mb-2"
                />
              </div>
            )}

            {/* Progress Bar */}
            {(recordingState.isRecording || recordingState.recordingTime > 0) && (
              <div className="mb-4">
                <div className="w-full bg-background rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-1000 ${
                      recordingState.isRecording ? 'bg-destructive' : 'bg-primary'
                    }`}
                    style={{ width: `${getProgressPercentage()}%` }}
                  />
                </div>
                <div className="text-xs text-secondary-foreground mt-1">
                  {formatTime(getRemainingTime())} remaining
                </div>
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div className="flex justify-center space-x-4 mb-6">
            {!recordingState.isRecording && !recordingState.audioBlob && (
              <button
                onClick={startRecording}
                className="w-16 h-16 rounded-full bg-primary hover:bg-primary-hover text-primary-foreground flex items-center justify-center transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <MicrophoneIcon className="w-8 h-8" />
              </button>
            )}

            {recordingState.isRecording && (
              <>
                <button
                  onClick={togglePauseRecording}
                  className="w-12 h-12 rounded-full bg-warning hover:bg-warning-hover text-warning-foreground flex items-center justify-center transition-all duration-200 shadow-lg"
                >
                  {recordingState.isPaused ? (
                    <PlayIcon className="w-6 h-6" />
                  ) : (
                    <PauseIcon className="w-6 h-6" />
                  )}
                </button>
                <button
                  onClick={stopRecording}
                  className={`w-16 h-16 rounded-full bg-destructive hover:bg-destructive-hover text-destructive-foreground flex items-center justify-center transition-all duration-200 shadow-lg ${
                    !recordingState.isPaused ? 'recording-pulse' : ''
                  }`}
                >
                  <StopIcon className="w-8 h-8" />
                </button>
              </>
            )}

            {recordingState.audioBlob && (
              <>
                <button
                  onClick={playRecording}
                  className="w-12 h-12 rounded-full bg-success hover:bg-success-hover text-success-foreground flex items-center justify-center transition-all duration-200"
                >
                  <PlayIcon className="w-6 h-6" />
                </button>
                <button
                  onClick={resetRecording}
                  className="w-12 h-12 rounded-full bg-muted hover:bg-muted-hover text-muted-foreground flex items-center justify-center transition-all duration-200"
                >
                  <ArrowPathIcon className="w-6 h-6" />
                </button>
              </>
            )}
          </div>

          {/* Audio Playback */}
          {recordingState.audioUrl && (
            <audio ref={audioRef} src={recordingState.audioUrl} controls className="w-full mb-4" />
          )}

          {/* Upload Section */}
          {recordingState.audioBlob && uploadStatus !== 'success' && (
            <div className="border-t pt-4">
              <button
                onClick={uploadRecording}
                disabled={uploadStatus === 'uploading'}
                className="w-full bg-info hover:bg-info-hover disabled:bg-muted text-info-foreground py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center"
              >
                {uploadStatus === 'uploading' ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Uploading... {Math.round(uploadProgress)}%</span>
                  </>
                ) : (
                  'Upload Recording'
                )}
              </button>
            </div>
          )}

          {/* Success Message */}
          {uploadStatus === 'success' && (
            <div className="bg-success-50 border border-success-border rounded-lg p-4 flex items-center text-success-foreground">
              <CheckCircleIcon className="w-5 h-5 mr-2" />
              {t('record-upload-success')}
            </div>
          )}

          {/* Error Message */}
          {error && uploadStatus === 'error' && (
            <div className="bg-destructive border border-destructive-border rounded-lg p-4 flex items-center text-destructive-foreground">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VoiceRecordingInterface;

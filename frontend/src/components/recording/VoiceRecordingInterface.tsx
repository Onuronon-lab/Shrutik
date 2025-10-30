import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  MicrophoneIcon, 
  StopIcon, 
  PlayIcon, 
  PauseIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/solid';
import { ClockIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import { Script, RecordingSession, VoiceRecording } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';
import AudioVisualizer from './AudioVisualizer';

type DurationOption = {
  value: '2_minutes' | '5_minutes' | '10_minutes';
  label: string;
  minutes: number;
  description: string;
};

const DURATION_OPTIONS: DurationOption[] = [
  { value: '2_minutes', label: '2 Minutes', minutes: 2, description: 'Quick recording session' },
  { value: '5_minutes', label: '5 Minutes', minutes: 5, description: 'Standard recording session' },
  { value: '10_minutes', label: '10 Minutes', minutes: 10, description: 'Extended recording session' }
];

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
  onRecordingComplete
}) => {
  // State management
  const [selectedDuration, setSelectedDuration] = useState<DurationOption | null>(null);
  const [currentScript, setCurrentScript] = useState<Script | null>(null);
  const [recordingSession, setRecordingSession] = useState<RecordingSession | null>(null);
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    recordingTime: 0,
    audioBlob: null,
    audioUrl: null
  });
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

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
  const handleDurationSelect = useCallback((duration: DurationOption) => {
    setSelectedDuration(duration);
    setCurrentScript(null);
    setRecordingSession(null);
    setRecordingState(prev => ({ ...prev, audioBlob: null, audioUrl: null }));
    setUploadStatus('idle');
    loadScript(duration);
  }, [loadScript]);

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

      mediaRecorder.ondataavailable = (event) => {
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
          isPaused: false
        }));
        
        cleanup();
      };

      mediaRecorder.start(1000);
      setRecordingState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        recordingTime: 0
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
    if (!recordingState.audioBlob || !recordingSession) {
      setError('No recording or session available');
      return;
    }

    setUploadStatus('uploading');
    setUploadProgress(0);
    setError(null);

    try {
      // Convert webm to wav for better compatibility
      const audioFile = new File([recordingState.audioBlob], 'recording.webm', {
        type: 'audio/webm'
      });

      const uploadData = {
        session_id: recordingSession.session_id,
        duration: recordingState.recordingTime,
        audio_format: 'webm',
        file_size: recordingState.audioBlob.size,
        sample_rate: 44100,
        channels: 1,
        bit_depth: 16
      };

      const recording = await apiService.uploadRecording(audioFile, uploadData);
      
      setUploadStatus('success');
      setUploadProgress(100);
      
      if (onRecordingComplete) {
        onRecordingComplete(recording);
      }

    } catch (err: any) {
      console.error('Upload error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload recording';
      setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to upload recording');
      setUploadStatus('error');
    }
  }, [recordingState.audioBlob, recordingState.recordingTime, recordingSession, onRecordingComplete]);

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
      audioUrl: null
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
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <ClockIcon className="w-5 h-5 mr-2" />
            Select Recording Duration
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {DURATION_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleDurationSelect(option)}
                className="p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all duration-200 text-left"
              >
                <div className="font-semibold text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600 mt-1">{option.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Script Display */}
      {selectedDuration && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <DocumentTextIcon className="w-5 h-5 mr-2" />
              Script ({selectedDuration.label})
            </h2>
            <button
              onClick={() => setSelectedDuration(null)}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Change Duration
            </button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="md" />
              <span className="ml-2 text-gray-600">Loading script...</span>
            </div>
          ) : currentScript ? (
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="text-lg leading-relaxed text-gray-900 font-bengali">
                {currentScript.text}
              </div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex items-center text-red-800">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                {error}
              </div>
              <button
                onClick={() => selectedDuration && loadScript(selectedDuration)}
                className="mt-2 text-sm text-red-600 hover:text-red-800"
              >
                Try Again
              </button>
            </div>
          ) : null}
        </div>
      )}

      {/* Recording Controls */}
      {currentScript && recordingSession && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recording Controls</h3>
          
          {/* Recording Status */}
          <div className="text-center mb-6">
            <div className="text-3xl font-mono font-bold text-gray-900 mb-2">
              {formatTime(recordingState.recordingTime)}
            </div>
            <div className="text-sm text-gray-500 mb-4">
              {recordingState.isRecording 
                ? (recordingState.isPaused ? 'Paused' : 'Recording...') 
                : recordingState.audioBlob 
                  ? 'Recording Complete' 
                  : 'Ready to Record'
              }
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
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-1000 ${
                      recordingState.isRecording ? 'bg-red-500' : 'bg-indigo-600'
                    }`}
                    style={{ width: `${getProgressPercentage()}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
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
                className="w-16 h-16 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <MicrophoneIcon className="w-8 h-8" />
              </button>
            )}

            {recordingState.isRecording && (
              <>
                <button
                  onClick={togglePauseRecording}
                  className="w-12 h-12 rounded-full bg-yellow-600 hover:bg-yellow-700 text-white flex items-center justify-center transition-all duration-200 shadow-lg"
                >
                  {recordingState.isPaused ? (
                    <PlayIcon className="w-6 h-6" />
                  ) : (
                    <PauseIcon className="w-6 h-6" />
                  )}
                </button>
                <button
                  onClick={stopRecording}
                  className={`w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center transition-all duration-200 shadow-lg ${
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
                  className="w-12 h-12 rounded-full bg-green-600 hover:bg-green-700 text-white flex items-center justify-center transition-all duration-200"
                >
                  <PlayIcon className="w-6 h-6" />
                </button>
                <button
                  onClick={resetRecording}
                  className="w-12 h-12 rounded-full bg-gray-600 hover:bg-gray-700 text-white flex items-center justify-center transition-all duration-200"
                >
                  <ArrowPathIcon className="w-6 h-6" />
                </button>
              </>
            )}
          </div>

          {/* Audio Playback */}
          {recordingState.audioUrl && (
            <audio
              ref={audioRef}
              src={recordingState.audioUrl}
              controls
              className="w-full mb-4"
            />
          )}

          {/* Upload Section */}
          {recordingState.audioBlob && uploadStatus !== 'success' && (
            <div className="border-t pt-4">
              <button
                onClick={uploadRecording}
                disabled={uploadStatus === 'uploading'}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center"
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
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center text-green-800">
              <CheckCircleIcon className="w-5 h-5 mr-2" />
              Recording uploaded successfully! It will be processed for transcription.
            </div>
          )}

          {/* Error Message */}
          {error && uploadStatus === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center text-red-800">
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
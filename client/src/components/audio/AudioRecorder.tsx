import React, { useCallback, useEffect } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
  maxDuration?: number; // in seconds
  className?: string;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onRecordingComplete,
  onRecordingStart,
  onRecordingStop,
  maxDuration = 600, // 10 minutes default
  className = '',
}) => {
  // Use the custom hook for audio recording logic
  const {
    isRecording,
    recordingTime,
    audioBlob,
    startRecording,
    stopRecording,
    formattedTime,
    progressPercentage,
    remainingTime,
  } = useAudioRecorder();

  // Handle recording completion
  useEffect(() => {
    if (audioBlob && !isRecording) {
      onRecordingComplete(audioBlob);
    }
  }, [audioBlob, isRecording, onRecordingComplete]);

  // Handle recording start/stop callbacks
  const handleStartRecording = useCallback(async () => {
    try {
      await startRecording(maxDuration);
      onRecordingStart?.();
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  }, [startRecording, maxDuration, onRecordingStart]);

  const handleStopRecording = useCallback(() => {
    stopRecording();
    onRecordingStop?.();
  }, [stopRecording, onRecordingStop]);

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <div className="text-center">
        <div className="mb-4">
          <button
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            className={`w-16 h-16 rounded-full flex items-center justify-center text-white transition-all duration-200 ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {isRecording ? (
              <StopIcon className="w-8 h-8" />
            ) : (
              <MicrophoneIcon className="w-8 h-8" />
            )}
          </button>
        </div>

        <div className="mb-4">
          <div className="text-2xl font-mono font-bold text-gray-900 mb-2">{formattedTime}</div>
          <div className="text-sm text-gray-500">
            {isRecording ? 'Recording...' : 'Click to start recording'}
          </div>
        </div>

        {isRecording && (
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${progressPercentage(maxDuration)}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {Math.floor(remainingTime(maxDuration) / 60)}:
              {(remainingTime(maxDuration) % 60).toString().padStart(2, '0')} remaining
            </div>
          </div>
        )}

        {!isRecording && recordingTime > 0 && (
          <div className="text-sm text-green-600">Recording completed ({formattedTime})</div>
        )}
      </div>
    </div>
  );
};

export default AudioRecorder;

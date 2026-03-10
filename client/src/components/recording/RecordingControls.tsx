import { useRef } from 'react';
import {
  MicrophoneIcon,
  StopIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/solid';
import LazyAudioVisualizer from './LazyAudioVisualizer';
import { useTranslation } from 'react-i18next';
import { StrictDurationOption } from '../../types/enhanced';

// Legacy interface for backward compatibility
interface LegacyRecordingState {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioBlob: Blob | null;
  audioUrl: string | null;
}

// Legacy props interface for backward compatibility
interface LegacyRecordingControlsProps {
  recordingState: LegacyRecordingState;
  selectedDuration: StrictDurationOption | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onTogglePause: () => void;
  onPlayRecording: () => void;
  onResetRecording: () => void;
  className?: string;
  'data-testid'?: string;
}

// Legacy component wrapper for backward compatibility
const RecordingControls: React.FC<LegacyRecordingControlsProps> = ({
  recordingState,
  selectedDuration,
  onStartRecording,
  onStopRecording,
  onTogglePause,
  onPlayRecording,
  onResetRecording,
  className = '',
  'data-testid': testId,
}) => {
  const { t } = useTranslation();
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Helper functions
  const formatTime = (seconds: number) =>
    `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
  const getProgressPercentage = () =>
    selectedDuration ? (recordingState.recordingTime / (selectedDuration.minutes * 60)) * 100 : 0;
  const getRemainingTime = () =>
    selectedDuration
      ? Math.max(0, selectedDuration.minutes * 60 - recordingState.recordingTime)
      : 0;

  const handlePlayRecording = () => {
    if (recordingState.audioUrl && audioRef.current) audioRef.current.play();
    onPlayRecording();
  };

  return (
    <div
      className={`bg-card rounded-lg shadow-md p-6 border border-border ${className}`}
      data-testid={testId}
    >
      <h3 className="text-lg font-semibold text-foreground mb-4">{t('record-control')}</h3>

      {/* Recording Status */}
      <div className="text-center mb-6">
        <div
          className="text-3xl font-mono font-bold text-foreground mb-2"
          data-testid="recording-time"
        >
          {formatTime(recordingState.recordingTime)}
        </div>
        <div className="text-sm text-secondary-foreground mb-4" data-testid="recording-status">
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
            <LazyAudioVisualizer
              isRecording={recordingState.isRecording && !recordingState.isPaused}
              className="mb-2"
            />
          </div>
        )}

        {/* Progress Bar */}
        {(recordingState.isRecording || recordingState.recordingTime > 0) && (
          <div className="mb-4" data-testid="progress-section">
            <div className="w-full bg-background rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-1000 ${recordingState.isRecording ? 'bg-destructive' : 'bg-primary'}`}
                style={{ width: `${getProgressPercentage()}%` }}
                data-testid="progress-bar"
              />
            </div>
            <div className="text-xs text-secondary-foreground mt-1" data-testid="remaining-time">
              {formatTime(getRemainingTime())} remaining
            </div>
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex justify-center space-x-4 mb-6">
        {!recordingState.isRecording && !recordingState.audioBlob && (
          <button
            onClick={onStartRecording}
            className="w-16 h-16 rounded-full bg-primary hover:bg-primary-hover text-primary-foreground flex items-center justify-center transition-all duration-200 shadow-lg hover:shadow-xl"
            data-testid="start-recording-button"
          >
            <MicrophoneIcon className="w-8 h-8" />
          </button>
        )}

        {recordingState.isRecording && (
          <>
            <button
              onClick={onTogglePause}
              className="w-12 h-12 rounded-full bg-warning hover:bg-warning-hover text-warning-foreground flex items-center justify-center transition-all duration-200 shadow-lg"
              data-testid="pause-resume-button"
            >
              {recordingState.isPaused ? (
                <PlayIcon className="w-6 h-6" />
              ) : (
                <PauseIcon className="w-6 h-6" />
              )}
            </button>
            <button
              onClick={onStopRecording}
              className={`w-16 h-16 rounded-full bg-destructive hover:bg-destructive-hover text-destructive-foreground flex items-center justify-center transition-all duration-200 shadow-lg ${
                !recordingState.isPaused ? 'recording-pulse' : ''
              }`}
              data-testid="stop-recording-button"
            >
              <StopIcon className="w-8 h-8" />
            </button>
          </>
        )}

        {recordingState.audioBlob && (
          <>
            <button
              onClick={handlePlayRecording}
              className="w-12 h-12 rounded-full bg-success hover:bg-success-hover text-success-foreground flex items-center justify-center transition-all duration-200"
              data-testid="play-recording-button"
            >
              <PlayIcon className="w-6 h-6" />
            </button>
            <button
              onClick={onResetRecording}
              className="w-12 h-12 rounded-full bg-muted hover:bg-muted-hover text-muted-foreground flex items-center justify-center transition-all duration-200"
              data-testid="reset-recording-button"
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
          src={recordingState.audioUrl || undefined}
          controls
          className="w-full mb-4"
          data-testid="audio-player"
        />
      )}
    </div>
  );
};

export default RecordingControls;

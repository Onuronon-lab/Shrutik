import React, { useCallback } from 'react';
import { MicrophoneIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import VoiceRecordingInterface from '../components/recording/VoiceRecordingInterface';
import ErrorBoundary from '../components/common/ErrorBoundary';
import { VoiceRecording } from '../types/api';
import { useTranslation } from 'react-i18next';
import { useUploadStore } from '../stores/uploadStore';

const RecordPage: React.FC = () => {
  const { t } = useTranslation();

  // Use Zustand store to track completed recordings
  const uploadState = useUploadStore(state => state.state);

  // Get recent successful uploads as completed recordings
  const completedRecordings: VoiceRecording[] =
    uploadState.status === 'success' ? [uploadState.recording] : [];

  const handleRecordingComplete = useCallback((_recording: VoiceRecording) => {
    // Recording completion is now handled by the upload store
    // This callback is maintained for backward compatibility
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <MicrophoneIcon className="mx-auto h-16 w-16 text-primary mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-2">
          {t('recordPage-voice-recording-title')}
        </h1>
        <p className="text-secondary-foreground">{t('recordPage-voice-recording-description')}</p>
      </div>

      {/* Recording Interface */}
      <ErrorBoundary>
        <VoiceRecordingInterface onRecordingComplete={handleRecordingComplete} />
      </ErrorBoundary>

      {/* Completed Recordings */}
      {completedRecordings.length > 0 && (
        <div className="mt-8 bg-card rounded-lg shadow-md p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
            <CheckCircleIcon className="w-5 h-5 mr-2 text-success" />
            Recent Recordings
          </h3>
          <div className="space-y-3">
            {completedRecordings.slice(0, 5).map(recording => (
              <div
                key={recording.id}
                className="flex items-center justify-between p-3 bg-background rounded-lg"
              >
                <div>
                  <div className="font-medium text-foreground">Recording #{recording.id}</div>
                  <div className="text-sm text-secondary-foreground">
                    Duration: {Math.round(recording.duration)}s • Status: {recording.status}
                  </div>
                </div>
                <div className="text-sm text-secondary-foreground">
                  {new Date(recording.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecordPage;

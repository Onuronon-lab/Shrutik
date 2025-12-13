import React, { useCallback, useEffect } from 'react';
import { VoiceRecording } from '../../types/api';
import { DurationOption } from '../../types/state';

import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import { useScriptManager } from '../../hooks/useScriptManager';
import { useUploadManager } from '../../hooks/useUploadManager';
import DurationSelector from './DurationSelector';
import ScriptViewer from './ScriptViewer';
import RecordingControls from './RecordingControls';
import UploadManager from './UploadManager';

interface VoiceRecordingInterfaceProps {
  onRecordingComplete?: (recording: VoiceRecording) => void;
}

const VoiceRecordingInterface: React.FC<VoiceRecordingInterfaceProps> = ({
  onRecordingComplete,
}) => {
  // Use custom hooks for business logic
  const audioRecorder = useAudioRecorder();
  const scriptManager = useScriptManager();
  const uploadManager = useUploadManager();

  // Handle successful upload
  useEffect(() => {
    if (uploadManager.isSuccess && uploadManager.uploadedRecording && onRecordingComplete) {
      onRecordingComplete(uploadManager.uploadedRecording);
    }
  }, [uploadManager.isSuccess, uploadManager.uploadedRecording, onRecordingComplete]);

  // Event handlers that delegate to hooks
  const handleDurationSelect = useCallback(
    (duration: DurationOption) => {
      scriptManager.selectDuration(duration);
      audioRecorder.resetRecording();
      uploadManager.reset();
    },
    [scriptManager, audioRecorder, uploadManager]
  );

  const handleChangeDuration = useCallback(() => {
    scriptManager.reset();
    audioRecorder.resetRecording();
    uploadManager.reset();
  }, [scriptManager, audioRecorder, uploadManager]);

  const handleRetryLoad = useCallback(() => {
    if (scriptManager.selectedDuration) {
      scriptManager.loadScript(scriptManager.selectedDuration);
    }
  }, [scriptManager]);

  // Recording event handlers
  const handleStartRecording = useCallback(() => {
    if (scriptManager.selectedDuration) {
      const maxDuration = scriptManager.selectedDuration.minutes * 60;
      audioRecorder.startRecording(maxDuration);
    }
  }, [audioRecorder, scriptManager.selectedDuration]);

  const handleTogglePause = useCallback(() => {
    if (audioRecorder.isPaused) {
      audioRecorder.resumeRecording();
    } else {
      audioRecorder.pauseRecording();
    }
  }, [audioRecorder]);

  // Upload event handler
  const handleUpload = useCallback(() => {
    if (audioRecorder.audioBlob && scriptManager.recordingSession) {
      uploadManager.uploadRecording(audioRecorder.audioBlob, {
        session_id: scriptManager.recordingSession.session_id,
        duration: audioRecorder.recordingTime,
        audio_format: 'webm',
        file_size: audioRecorder.audioBlob.size,
        sample_rate: 48000,
        channels: 1,
        bit_depth: 16,
      });
    }
  }, [
    audioRecorder.audioBlob,
    audioRecorder.recordingTime,
    scriptManager.recordingSession,
    uploadManager,
  ]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Duration Selection */}
      {!scriptManager.selectedDuration && (
        <DurationSelector onDurationSelect={handleDurationSelect} />
      )}

      {/* Script Display */}
      {scriptManager.selectedDuration && (
        <ScriptViewer
          selectedDuration={scriptManager.selectedDuration}
          currentScript={scriptManager.currentScript}
          isLoading={scriptManager.isLoading}
          error={scriptManager.error}
          onChangeDuration={handleChangeDuration}
          onRetryLoad={handleRetryLoad}
        />
      )}

      {/* Recording Controls */}
      {scriptManager.canRecord && (
        <RecordingControls
          recordingState={{
            isRecording: audioRecorder.isRecording,
            isPaused: audioRecorder.isPaused,
            recordingTime: audioRecorder.recordingTime,
            audioBlob: audioRecorder.audioBlob,
            audioUrl: audioRecorder.audioUrl,
          }}
          selectedDuration={scriptManager.selectedDuration}
          onStartRecording={handleStartRecording}
          onStopRecording={audioRecorder.stopRecording}
          onTogglePause={handleTogglePause}
          onPlayRecording={audioRecorder.playRecording}
          onResetRecording={audioRecorder.resetRecording}
        />
      )}

      {/* Upload Manager */}
      {scriptManager.canRecord && (
        <UploadManager
          hasRecording={!!audioRecorder.audioBlob}
          uploadStatus={
            uploadManager.isUploading
              ? 'uploading'
              : uploadManager.isSuccess
                ? 'success'
                : uploadManager.isError
                  ? 'error'
                  : 'idle'
          }
          uploadProgress={uploadManager.progress}
          error={uploadManager.errorMessage}
          onUpload={handleUpload}
        />
      )}
    </div>
  );
};

export default VoiceRecordingInterface;

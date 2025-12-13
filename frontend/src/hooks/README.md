# Custom Hooks

This directory contains custom React hooks that extract reusable logic from components, following the frontend modernization requirements.

## Available Hooks

### Core Recording Hooks

- **`useAudioRecorder`** - Manages audio recording state and operations
- **`useScriptManager`** - Handles script fetching and caching logic
- **`useUploadManager`** - Manages upload progress and error states
- **`useDurationSelector`** - Handles duration selection and validation

### Utility Hooks

- **`useAsync`** - Generic async operation handler
- **`useAsyncResource`** - Resource loading with caching
- **`useErrorHandler`** - Centralized error handling
- **`useModal`** - Modal state management
- **`useTheme`** - Theme switching functionality

## Usage Example

Here's how to use the new custom hooks together in a component:

```typescript
import React from 'react';
import {
  useAudioRecorder,
  useScriptManager,
  useUploadManager,
  useDurationSelector
} from '../hooks';

const ModernRecordingComponent: React.FC = () => {
  // Duration selection
  const {
    selectedDuration,
    availableOptions,
    selectDuration,
    hasSelection,
    maxRecordingTime
  } = useDurationSelector();

  // Script management
  const {
    currentScript,
    isLoading: scriptLoading,
    error: scriptError,
    recordingSession,
    canRecord
  } = useScriptManager();

  // Audio recording
  const {
    isRecording,
    isPaused,
    isCompleted,
    audioBlob,
    formattedTime,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording
  } = useAudioRecorder();

  // Upload management
  const {
    isUploading,
    isSuccess,
    errorMessage: uploadError,
    progress,
    uploadRecording
  } = useUploadManager();

  // Handle duration selection
  const handleDurationSelect = async (duration: DurationOption) => {
    await selectDuration(duration);
  };

  // Handle recording start
  const handleStartRecording = async () => {
    if (canRecord && maxRecordingTime) {
      await startRecording(maxRecordingTime);
    }
  };

  // Handle upload
  const handleUpload = async () => {
    if (audioBlob && recordingSession) {
      const metadata = {
        session_id: recordingSession.session_id,
        duration: recordingTime,
        audio_format: 'webm',
        file_size: audioBlob.size,
        sample_rate: 48000,
        channels: 1,
        bit_depth: 16,
      };

      await uploadRecording(audioBlob, metadata);
    }
  };

  return (
    <div>
      {/* Duration Selection */}
      {!hasSelection && (
        <div>
          <h2>Select Duration</h2>
          {availableOptions.map(option => (
            <button
              key={option.value}
              onClick={() => handleDurationSelect(option)}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}

      {/* Script Display */}
      {hasSelection && (
        <div>
          {scriptLoading && <p>Loading script...</p>}
          {scriptError && <p>Error: {scriptError}</p>}
          {currentScript && (
            <div>
              <h3>Script</h3>
              <p>{currentScript.text}</p>
            </div>
          )}
        </div>
      )}

      {/* Recording Controls */}
      {canRecord && (
        <div>
          <p>Time: {formattedTime}</p>

          {!isRecording && !isCompleted && (
            <button onClick={handleStartRecording}>Start Recording</button>
          )}

          {isRecording && (
            <>
              <button onClick={isPaused ? resumeRecording : pauseRecording}>
                {isPaused ? 'Resume' : 'Pause'}
              </button>
              <button onClick={stopRecording}>Stop</button>
            </>
          )}

          {isCompleted && (
            <>
              <button onClick={resetRecording}>Record Again</button>
              <button onClick={handleUpload} disabled={isUploading}>
                {isUploading ? `Uploading... ${progress}%` : 'Upload'}
              </button>
            </>
          )}
        </div>
      )}

      {/* Upload Status */}
      {isSuccess && <p>Upload successful!</p>}
      {uploadError && <p>Upload error: {uploadError}</p>}
    </div>
  );
};
```

## Benefits

1. **Reusability** - Logic can be shared across multiple components
2. **Testability** - Each hook can be tested in isolation
3. **Separation of Concerns** - UI logic separated from business logic
4. **Type Safety** - Full TypeScript support with proper interfaces
5. **Consistency** - Standardized patterns across the application

## Integration with Zustand Stores

These hooks integrate seamlessly with the existing Zustand stores:

- `useAudioRecorder` → `useRecordingStore`
- `useScriptManager` → `useScriptStore` + `useSessionStore`
- `useUploadManager` → `useUploadStore`
- `useDurationSelector` → `useScriptStore`

The hooks provide a higher-level API while maintaining the benefits of centralized state management.

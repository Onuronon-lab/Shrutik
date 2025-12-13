# Zustand State Management

This directory contains the centralized state management implementation using Zustand for the frontend application.

## Overview

The state management is organized into four main stores:

- **RecordingStore**: Manages audio recording state and operations
- **ScriptStore**: Handles script loading and duration selection
- **UploadStore**: Manages file upload progress and status
- **SessionStore**: Manages recording session data
- **AppStore**: Provides global actions that coordinate between stores

## Store Structure

### RecordingStore (`recordingStore.ts`)

Manages all recording-related state:

```typescript
interface RecordingState {
  status: RecordingStatus; // 'idle' | 'recording' | 'paused' | 'completed'
  recordingTime: number;
  audioBlob: Blob | null;
  audioUrl: string | null;
  mediaRecorder: MediaRecorder | null;
  stream: MediaStream | null;
}
```

**Key Actions:**

- `setStatus(status)` - Update recording status
- `setRecordingTime(time)` - Set recording time
- `incrementRecordingTime()` - Increment time by 1 second
- `setAudioBlob(blob)` - Store recorded audio blob
- `setAudioUrl(url)` - Set audio URL for playback
- `reset()` - Reset to initial state
- `cleanup()` - Clean up resources (URLs, streams)

### ScriptStore (`scriptStore.ts`)

Manages script loading and selection:

```typescript
interface ScriptState {
  current: Script | null;
  selectedDuration: DurationOption | null;
  isLoading: boolean;
  error: string | null;
}
```

**Key Actions:**

- `setCurrentScript(script)` - Set the current script
- `setSelectedDuration(duration)` - Set selected duration
- `setLoading(loading)` - Set loading state
- `setError(error)` - Set error message
- `reset()` - Reset to initial state

**Persistence:** The `selectedDuration` is persisted to localStorage.

### UploadStore (`uploadStore.ts`)

Manages file upload operations:

```typescript
type UploadState =
  | { status: 'idle' }
  | { status: 'uploading'; progress: number }
  | { status: 'success'; recording: VoiceRecording }
  | { status: 'error'; error: string };
```

**Key Actions:**

- `setIdle()` - Reset to idle state
- `setUploading(progress)` - Start upload with progress
- `setSuccess(recording)` - Mark upload as successful
- `setError(error)` - Set error state
- `updateProgress(progress)` - Update upload progress
- `reset()` - Reset to initial state

### SessionStore (`sessionStore.ts`)

Manages recording session data:

```typescript
interface SessionState {
  current: RecordingSession | null;
  isCreating: boolean;
  error: string | null;
}
```

**Key Actions:**

- `setCurrent(session)` - Set current session
- `setCreating(creating)` - Set session creation state
- `setError(error)` - Set error message
- `reset()` - Reset to initial state

**Persistence:** The `current` session is persisted to localStorage.

### AppStore (`appStore.ts`)

Provides global coordination actions:

**Key Actions:**

- `resetAll()` - Reset all stores to initial state
- `startNewRecordingSession()` - Reset recording and upload stores for new session

## Usage Examples

### Basic Usage

```typescript
import { useRecordingStore, useScriptStore } from '../stores';

function MyComponent() {
  const recordingState = useRecordingStore();
  const scriptState = useScriptStore();

  const startRecording = () => {
    recordingState.setStatus({ type: 'recording', startTime: Date.now() });
  };

  return (
    <div>
      <p>Status: {recordingState.status.type}</p>
      <p>Time: {recordingState.recordingTime}s</p>
      <button onClick={startRecording}>Start Recording</button>
    </div>
  );
}
```

### Selective Subscriptions

```typescript
// Subscribe only to specific state slices for better performance
const recordingTime = useRecordingStore(state => state.recordingTime);
const isLoading = useScriptStore(state => state.isLoading);
```

### Using Actions

```typescript
const { setRecordingTime, incrementRecordingTime } = useRecordingStore();

// Set specific time
setRecordingTime(30);

// Increment by 1 second
incrementRecordingTime();
```

## Best Practices

### 1. Resource Cleanup

Always clean up resources when components unmount:

```typescript
useEffect(() => {
  return () => {
    useRecordingStore.getState().cleanup();
  };
}, []);
```

### 2. Error Handling

Use the error states in stores for consistent error handling:

```typescript
const { error, setError } = useScriptStore();

const loadScript = async () => {
  try {
    // ... load script
  } catch (err) {
    setError(err.message);
  }
};
```

### 3. Performance Optimization

Use selective subscriptions to avoid unnecessary re-renders:

```typescript
// Good - only re-renders when recordingTime changes
const recordingTime = useRecordingStore(state => state.recordingTime);

// Avoid - re-renders on any state change
const recordingState = useRecordingStore();
```

### 4. Global Actions

Use the AppStore for actions that need to coordinate multiple stores:

```typescript
const { resetAll, startNewRecordingSession } = useAppStore();

// Reset everything
resetAll();

// Start fresh recording session
startNewRecordingSession();
```

## Testing

The stores include comprehensive tests in `__tests__/stores.test.ts`. Run tests with:

```bash
npm test -- --run src/stores
```

## DevTools

All stores are configured with Zustand DevTools for debugging. Open Redux DevTools in your browser to inspect state changes.

## Migration from useState

When migrating from local `useState` to Zustand stores:

1. Replace `useState` hooks with store subscriptions
2. Move state update logic to store actions
3. Use store actions instead of local state setters
4. Remove local state initialization

### Before (useState):

```typescript
const [isRecording, setIsRecording] = useState(false);
const [recordingTime, setRecordingTime] = useState(0);
```

### After (Zustand):

```typescript
const { status, recordingTime, setStatus, setRecordingTime } = useRecordingStore();
const isRecording = status.type === 'recording';
```

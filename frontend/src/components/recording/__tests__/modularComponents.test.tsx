import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, expect, describe, it } from 'vitest';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../../i18n';
import DurationSelector from '../DurationSelector';
import ScriptViewer from '../ScriptViewer';
import RecordingControls from '../RecordingControls';
import UploadManager from '../UploadManager';
import * as fc from 'fast-check';

// Mock the LoadingSpinner component
vi.mock('../../common/LoadingSpinner', () => ({
  default: ({ size }: { size: string }) => <div data-testid="loading-spinner">{size}</div>,
}));

// Mock the AudioVisualizer component
vi.mock('../AudioVisualizer', () => ({
  default: ({ isRecording }: { isRecording: boolean }) => (
    <div data-testid="audio-visualizer">{isRecording ? 'Recording' : 'Not Recording'}</div>
  ),
}));

const renderWithI18n = (component: React.ReactElement) => {
  return render(<I18nextProvider i18n={i18n}>{component}</I18nextProvider>);
};

describe('Modular Recording Components', () => {
  describe('DurationSelector', () => {
    it('should render duration options and handle selection', () => {
      const mockOnDurationSelect = vi.fn();

      renderWithI18n(<DurationSelector onDurationSelect={mockOnDurationSelect} />);

      // Check if duration options are rendered
      expect(screen.getByTestId('duration-option-2_minutes')).toBeInTheDocument();
      expect(screen.getByTestId('duration-option-5_minutes')).toBeInTheDocument();
      expect(screen.getByTestId('duration-option-10_minutes')).toBeInTheDocument();

      // Test selection
      fireEvent.click(screen.getByTestId('duration-option-5_minutes'));
      expect(mockOnDurationSelect).toHaveBeenCalledWith(
        expect.objectContaining({ value: '5_minutes' })
      );
    });

    it('should display correct duration information for each option', () => {
      const mockOnDurationSelect = vi.fn();

      renderWithI18n(<DurationSelector onDurationSelect={mockOnDurationSelect} />);

      // Check 2 minutes option
      const twoMinOption = screen.getByTestId('duration-option-2_minutes');
      expect(twoMinOption).toHaveTextContent('2 Minutes');
      expect(twoMinOption).toHaveTextContent('Max file size: 10MB');

      // Check 5 minutes option
      const fiveMinOption = screen.getByTestId('duration-option-5_minutes');
      expect(fiveMinOption).toHaveTextContent('5 Minutes');
      expect(fiveMinOption).toHaveTextContent('Max file size: 25MB');

      // Check 10 minutes option
      const tenMinOption = screen.getByTestId('duration-option-10_minutes');
      expect(tenMinOption).toHaveTextContent('10 Minutes');
      expect(tenMinOption).toHaveTextContent('Max file size: 50MB');
    });

    it('should apply custom className and data-testid', () => {
      const mockOnDurationSelect = vi.fn();

      renderWithI18n(
        <DurationSelector
          onDurationSelect={mockOnDurationSelect}
          className="custom-class"
          data-testid="custom-duration-selector"
        />
      );

      const container = screen.getByTestId('custom-duration-selector');
      expect(container).toHaveClass('custom-class');
    });
  });

  describe('ScriptViewer', () => {
    const mockDuration = {
      value: '5_minutes' as const,
      label: '5 Minutes',
      minutes: 5,
      description: 'Standard session',
    };

    it('should show loading state', () => {
      renderWithI18n(
        <ScriptViewer
          selectedDuration={mockDuration}
          currentScript={null}
          isLoading={true}
          error={null}
          onChangeDuration={vi.fn()}
          onRetryLoad={vi.fn()}
        />
      );

      expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('should show script content when loaded', () => {
      const mockScript = {
        id: 1,
        text: 'Test script content',
        duration_category: '5_minutes' as const,
        language_id: 1,
        meta_data: {},
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
      };

      renderWithI18n(
        <ScriptViewer
          selectedDuration={mockDuration}
          currentScript={mockScript}
          isLoading={false}
          error={null}
          onChangeDuration={vi.fn()}
          onRetryLoad={vi.fn()}
        />
      );

      expect(screen.getByTestId('script-content')).toBeInTheDocument();
      expect(screen.getByText('Test script content')).toBeInTheDocument();
    });

    it('should show error state with retry option', () => {
      const mockOnRetryLoad = vi.fn();

      renderWithI18n(
        <ScriptViewer
          selectedDuration={mockDuration}
          currentScript={null}
          isLoading={false}
          error="Failed to load script"
          onChangeDuration={vi.fn()}
          onRetryLoad={mockOnRetryLoad}
        />
      );

      expect(screen.getByTestId('error-state')).toBeInTheDocument();
      expect(screen.getByText('Failed to load script')).toBeInTheDocument();

      fireEvent.click(screen.getByTestId('retry-button'));
      expect(mockOnRetryLoad).toHaveBeenCalled();
    });
  });

  describe('RecordingControls', () => {
    const mockRecordingState = {
      isRecording: false,
      isPaused: false,
      recordingTime: 0,
      audioBlob: null,
      audioUrl: null,
    };

    const mockDuration = {
      value: '5_minutes' as const,
      label: '5 Minutes',
      minutes: 5,
      description: 'Standard session',
    };

    it('should show start recording button when ready', () => {
      const mockOnStartRecording = vi.fn();

      renderWithI18n(
        <RecordingControls
          recordingState={mockRecordingState}
          selectedDuration={mockDuration}
          onStartRecording={mockOnStartRecording}
          onStopRecording={vi.fn()}
          onTogglePause={vi.fn()}
          onPlayRecording={vi.fn()}
          onResetRecording={vi.fn()}
        />
      );

      const startButton = screen.getByTestId('start-recording-button');
      expect(startButton).toBeInTheDocument();

      fireEvent.click(startButton);
      expect(mockOnStartRecording).toHaveBeenCalled();
    });

    it('should show recording controls when recording', () => {
      const recordingState = {
        ...mockRecordingState,
        isRecording: true,
        recordingTime: 30,
      };

      renderWithI18n(
        <RecordingControls
          recordingState={recordingState}
          selectedDuration={mockDuration}
          onStartRecording={vi.fn()}
          onStopRecording={vi.fn()}
          onTogglePause={vi.fn()}
          onPlayRecording={vi.fn()}
          onResetRecording={vi.fn()}
        />
      );

      expect(screen.getByTestId('pause-resume-button')).toBeInTheDocument();
      expect(screen.getByTestId('stop-recording-button')).toBeInTheDocument();
      expect(screen.getByTestId('progress-section')).toBeInTheDocument();
    });

    it('should display correct recording time and progress', () => {
      const recordingState = {
        ...mockRecordingState,
        isRecording: true,
        recordingTime: 125, // 2:05
      };

      renderWithI18n(
        <RecordingControls
          recordingState={recordingState}
          selectedDuration={mockDuration}
          onStartRecording={vi.fn()}
          onStopRecording={vi.fn()}
          onTogglePause={vi.fn()}
          onPlayRecording={vi.fn()}
          onResetRecording={vi.fn()}
        />
      );

      expect(screen.getByTestId('recording-time')).toHaveTextContent('2:05');
      expect(screen.getByTestId('remaining-time')).toHaveTextContent('2:55 remaining');
    });

    it('should show paused state correctly', () => {
      const recordingState = {
        ...mockRecordingState,
        isRecording: true,
        isPaused: true,
        recordingTime: 60,
      };

      renderWithI18n(
        <RecordingControls
          recordingState={recordingState}
          selectedDuration={mockDuration}
          onStartRecording={vi.fn()}
          onStopRecording={vi.fn()}
          onTogglePause={vi.fn()}
          onPlayRecording={vi.fn()}
          onResetRecording={vi.fn()}
        />
      );

      expect(screen.getByTestId('recording-status')).toHaveTextContent('Paused');
    });

    it('should show playback controls when recording is complete', () => {
      const mockBlob = new Blob(['audio data'], { type: 'audio/webm' });
      const recordingState = {
        ...mockRecordingState,
        audioBlob: mockBlob,
        audioUrl: 'blob:audio-url',
      };

      const mockOnPlayRecording = vi.fn();
      const mockOnResetRecording = vi.fn();

      renderWithI18n(
        <RecordingControls
          recordingState={recordingState}
          selectedDuration={mockDuration}
          onStartRecording={vi.fn()}
          onStopRecording={vi.fn()}
          onTogglePause={vi.fn()}
          onPlayRecording={mockOnPlayRecording}
          onResetRecording={mockOnResetRecording}
        />
      );

      expect(screen.getByTestId('play-recording-button')).toBeInTheDocument();
      expect(screen.getByTestId('reset-recording-button')).toBeInTheDocument();
      expect(screen.getByTestId('audio-player')).toBeInTheDocument();

      fireEvent.click(screen.getByTestId('play-recording-button'));
      expect(mockOnPlayRecording).toHaveBeenCalled();

      fireEvent.click(screen.getByTestId('reset-recording-button'));
      expect(mockOnResetRecording).toHaveBeenCalled();
    });
  });

  describe('UploadManager', () => {
    it('should not render when no recording exists', () => {
      const { container } = renderWithI18n(
        <UploadManager
          hasRecording={false}
          uploadStatus="idle"
          uploadProgress={0}
          error={null}
          onUpload={vi.fn()}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should show upload button when recording exists', () => {
      const mockOnUpload = vi.fn();

      renderWithI18n(
        <UploadManager
          hasRecording={true}
          uploadStatus="idle"
          uploadProgress={0}
          error={null}
          onUpload={mockOnUpload}
        />
      );

      const uploadButton = screen.getByTestId('upload-button');
      expect(uploadButton).toBeInTheDocument();
      expect(uploadButton).toHaveTextContent('Upload Recording');

      fireEvent.click(uploadButton);
      expect(mockOnUpload).toHaveBeenCalled();
    });

    it('should show uploading state with progress', () => {
      renderWithI18n(
        <UploadManager
          hasRecording={true}
          uploadStatus="uploading"
          uploadProgress={45}
          error={null}
          onUpload={vi.fn()}
        />
      );

      const uploadButton = screen.getByTestId('upload-button');
      expect(uploadButton).toBeDisabled();
      expect(uploadButton).toHaveTextContent('Uploading... 45%');
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('should show success message when upload completes', () => {
      renderWithI18n(
        <UploadManager
          hasRecording={true}
          uploadStatus="success"
          uploadProgress={100}
          error={null}
          onUpload={vi.fn()}
        />
      );

      expect(screen.getByTestId('success-message')).toBeInTheDocument();
      expect(screen.queryByTestId('upload-button')).not.toBeInTheDocument();
    });

    it('should show error message when upload fails', () => {
      renderWithI18n(
        <UploadManager
          hasRecording={true}
          uploadStatus="error"
          uploadProgress={0}
          error="Upload failed"
          onUpload={vi.fn()}
        />
      );

      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
    });

    it('should handle custom className and data-testid', () => {
      renderWithI18n(
        <UploadManager
          hasRecording={true}
          uploadStatus="idle"
          uploadProgress={0}
          error={null}
          onUpload={vi.fn()}
          className="custom-upload-class"
          data-testid="custom-upload-manager"
        />
      );

      const container = screen.getByTestId('custom-upload-manager');
      expect(container).toHaveClass('custom-upload-class');
    });
  });

  // **Feature: frontend-modernization, Property 4: Component modularity and single responsibility**
  describe('Property 4: Component modularity and single responsibility', () => {
    it('should maintain component isolation and single responsibility', () => {
      fc.assert(
        fc.property(
          // Generate arbitrary props for each component
          fc.record({
            className: fc.option(fc.string(), { nil: undefined }),
            'data-testid': fc.option(fc.string(), { nil: undefined }),
          }),
          fc.boolean(),
          fc.constantFrom('idle', 'uploading', 'success', 'error'),
          fc.integer({ min: 0, max: 100 }),
          fc.option(fc.string(), { nil: null }),
          (commonProps, hasRecording, uploadStatus, uploadProgress, error) => {
            // Test that each component can render independently without coupling
            const mockCallbacks = {
              onDurationSelect: vi.fn(),
              onChangeDuration: vi.fn(),
              onRetryLoad: vi.fn(),
              onStartRecording: vi.fn(),
              onStopRecording: vi.fn(),
              onTogglePause: vi.fn(),
              onPlayRecording: vi.fn(),
              onResetRecording: vi.fn(),
              onUpload: vi.fn(),
            };

            const mockDuration = {
              value: '5_minutes' as const,
              label: '5 Minutes',
              minutes: 5,
              description: 'Standard session',
            };

            const mockScript = {
              id: 1,
              text: 'Test script',
              duration_category: '5_minutes' as const,
              language_id: 1,
              meta_data: {},
              created_at: '2023-01-01',
              updated_at: '2023-01-01',
            };

            const mockRecordingState = {
              isRecording: false,
              isPaused: false,
              recordingTime: 0,
              audioBlob: null,
              audioUrl: null,
            };

            // Test 1: DurationSelector should render independently
            const durationSelectorResult = render(
              <I18nextProvider i18n={i18n}>
                <DurationSelector
                  onDurationSelect={mockCallbacks.onDurationSelect}
                  {...commonProps}
                />
              </I18nextProvider>
            );

            // Should render without errors and have its specific functionality
            expect(durationSelectorResult.container.firstChild).toBeTruthy();
            durationSelectorResult.unmount();

            // Test 2: ScriptViewer should render independently
            const scriptViewerResult = render(
              <I18nextProvider i18n={i18n}>
                <ScriptViewer
                  selectedDuration={mockDuration}
                  currentScript={mockScript}
                  isLoading={false}
                  error={error}
                  onChangeDuration={mockCallbacks.onChangeDuration}
                  onRetryLoad={mockCallbacks.onRetryLoad}
                  {...commonProps}
                />
              </I18nextProvider>
            );

            // Should render without errors and have its specific functionality
            expect(scriptViewerResult.container.firstChild).toBeTruthy();
            scriptViewerResult.unmount();

            // Test 3: RecordingControls should render independently
            const recordingControlsResult = render(
              <I18nextProvider i18n={i18n}>
                <RecordingControls
                  recordingState={mockRecordingState}
                  selectedDuration={mockDuration}
                  onStartRecording={mockCallbacks.onStartRecording}
                  onStopRecording={mockCallbacks.onStopRecording}
                  onTogglePause={mockCallbacks.onTogglePause}
                  onPlayRecording={mockCallbacks.onPlayRecording}
                  onResetRecording={mockCallbacks.onResetRecording}
                  {...commonProps}
                />
              </I18nextProvider>
            );

            // Should render without errors and have its specific functionality
            expect(recordingControlsResult.container.firstChild).toBeTruthy();
            recordingControlsResult.unmount();

            // Test 4: UploadManager should render independently
            const uploadManagerResult = render(
              <I18nextProvider i18n={i18n}>
                <UploadManager
                  hasRecording={hasRecording}
                  uploadStatus={uploadStatus}
                  uploadProgress={uploadProgress}
                  error={error}
                  onUpload={mockCallbacks.onUpload}
                  {...commonProps}
                />
              </I18nextProvider>
            );

            // Should render without errors (or render null if no recording)
            if (hasRecording) {
              expect(uploadManagerResult.container.firstChild).toBeTruthy();
            } else {
              expect(uploadManagerResult.container.firstChild).toBeNull();
            }
            uploadManagerResult.unmount();

            // Test 5: Components should not interfere with each other when rendered together
            const combinedResult = render(
              <I18nextProvider i18n={i18n}>
                <div>
                  <DurationSelector
                    onDurationSelect={mockCallbacks.onDurationSelect}
                    {...commonProps}
                  />
                  <ScriptViewer
                    selectedDuration={mockDuration}
                    currentScript={mockScript}
                    isLoading={false}
                    error={error}
                    onChangeDuration={mockCallbacks.onChangeDuration}
                    onRetryLoad={mockCallbacks.onRetryLoad}
                    {...commonProps}
                  />
                  <RecordingControls
                    recordingState={mockRecordingState}
                    selectedDuration={mockDuration}
                    onStartRecording={mockCallbacks.onStartRecording}
                    onStopRecording={mockCallbacks.onStopRecording}
                    onTogglePause={mockCallbacks.onTogglePause}
                    onPlayRecording={mockCallbacks.onPlayRecording}
                    onResetRecording={mockCallbacks.onResetRecording}
                    {...commonProps}
                  />
                  <UploadManager
                    hasRecording={hasRecording}
                    uploadStatus={uploadStatus}
                    uploadProgress={uploadProgress}
                    error={error}
                    onUpload={mockCallbacks.onUpload}
                    {...commonProps}
                  />
                </div>
              </I18nextProvider>
            );

            // All components should render together without conflicts
            expect(combinedResult.container.firstChild).toBeTruthy();
            combinedResult.unmount();
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

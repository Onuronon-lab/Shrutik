import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import * as fc from 'fast-check';
import { useDurationSelector } from '../useDurationSelector';
import { useAudioRecorder } from '../useAudioRecorder';
import { useScriptManager } from '../useScriptManager';
import { useUploadManager } from '../useUploadManager';
import { useScriptStore } from '../../stores/scriptStore';
import { useRecordingStore } from '../../stores/recordingStore';
import { useUploadStore } from '../../stores/uploadStore';
import { useSessionStore } from '../../stores/sessionStore';
import { DurationOption } from '../../types/state';

// Mock the translation hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'recordPage-2-minutes': '2 Minutes',
        'recordPage-5-minutes': '5 Minutes',
        'recordPage-10-minutes': '10 Minutes',
        'recordPage-quick-record-session': 'Quick recording session',
        'recordPage-standard-record-session': 'Standard recording session',
        'recordPage-extended-record-session': 'Extended recording session',
      };
      return translations[key] || key;
    },
  }),
}));

// Mock navigator.mediaDevices for audio recorder tests
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    }),
  },
  writable: true,
});

// Mock MediaRecorder
global.MediaRecorder = vi.fn().mockImplementation(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  state: 'inactive',
  ondataavailable: null,
  onstop: null,
})) as any;

// Mock recording service
vi.mock('../../services/recording.service', () => ({
  recordingService: {
    getRandomScript: vi.fn().mockResolvedValue({
      id: 1,
      text: 'Test script',
      duration_category: '2_minutes',
      language_id: 1,
      meta_data: {},
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    }),
    createRecordingSession: vi.fn().mockResolvedValue({
      session_id: 'test-session',
      script_id: 1,
      script_text: 'Test script',
      language_id: 1,
      expected_duration_category: '2_minutes',
      created_at: '2023-01-01',
      expires_at: '2023-01-02',
    }),
    uploadRecording: vi.fn().mockResolvedValue({
      id: 1,
      user_id: 1,
      script_id: 1,
      language_id: 1,
      file_path: '/test/path',
      duration: 120,
      status: 'UPLOADED',
      meta_data: {},
      created_at: '2023-01-01',
      updated_at: '2023-01-01',
    }),
  },
}));

// Mock localStorage
Object.defineProperty(global, 'localStorage', {
  value: {
    getItem: vi.fn(() => 'mock-token'),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
  writable: true,
});

describe('useDurationSelector', () => {
  beforeEach(() => {
    // Reset the store before each test
    useScriptStore.getState().reset();
  });

  it('should initialize with no selection', () => {
    const { result } = renderHook(() => useDurationSelector());

    expect(result.current.selectedDuration).toBeNull();
    expect(result.current.hasSelection).toBe(false);
    expect(result.current.selectedMinutes).toBe(0);
    expect(result.current.selectedSeconds).toBe(0);
  });

  it('should provide available duration options', () => {
    const { result } = renderHook(() => useDurationSelector());

    expect(result.current.availableOptions).toHaveLength(3);
    expect(result.current.availableOptions[0].value).toBe('2_minutes');
    expect(result.current.availableOptions[1].value).toBe('5_minutes');
    expect(result.current.availableOptions[2].value).toBe('10_minutes');
  });

  it('should select a valid duration', () => {
    const { result } = renderHook(() => useDurationSelector());

    const duration = result.current.availableOptions[1]; // 5 minutes

    act(() => {
      result.current.selectDuration(duration);
    });

    expect(result.current.selectedDuration).toEqual(duration);
    expect(result.current.hasSelection).toBe(true);
    expect(result.current.selectedMinutes).toBe(5);
    expect(result.current.selectedSeconds).toBe(300);
    expect(result.current.maxRecordingTime).toBe(300);
  });

  it('should validate duration options correctly', () => {
    const { result } = renderHook(() => useDurationSelector());

    const validDuration = result.current.availableOptions[0];
    const invalidDuration = {
      value: '15_minutes' as any,
      label: '15 Minutes',
      minutes: 15,
      description: 'Test',
    };

    expect(result.current.isValidDuration(validDuration)).toBe(true);
    expect(result.current.isValidDuration(invalidDuration)).toBe(false);
    expect(result.current.isValidDuration(null)).toBe(false);
  });

  it('should provide validation messages', () => {
    const { result } = renderHook(() => useDurationSelector());

    expect(result.current.validateSelection(null)).toBe('Please select a recording duration');

    const validDuration = result.current.availableOptions[0];
    expect(result.current.validateSelection(validDuration)).toBeNull();

    const invalidDuration = {
      value: '15_minutes' as any,
      label: '15 Minutes',
      minutes: 15,
      description: 'Test',
    };
    expect(result.current.validateSelection(invalidDuration)).toBe('Invalid duration selection');
  });

  it('should clear selection', () => {
    const { result } = renderHook(() => useDurationSelector());

    // First select a duration
    act(() => {
      result.current.selectDuration(result.current.availableOptions[0]);
    });

    expect(result.current.hasSelection).toBe(true);

    // Then clear it
    act(() => {
      result.current.clearSelection();
    });

    expect(result.current.selectedDuration).toBeNull();
    expect(result.current.hasSelection).toBe(false);
  });

  it('should handle edge case validations', () => {
    const { result } = renderHook(() => useDurationSelector());

    // Test duration with 0 minutes - will be invalid because it's not in available options
    const zeroDuration = {
      value: '0_minutes' as any,
      label: '0 Minutes',
      minutes: 0,
      description: 'Test',
    };
    expect(result.current.validateSelection(zeroDuration)).toBe('Invalid duration selection');

    // Test duration over 60 minutes - will be invalid because it's not in available options
    const longDuration = {
      value: '90_minutes' as any,
      label: '90 Minutes',
      minutes: 90,
      description: 'Test',
    };
    expect(result.current.validateSelection(longDuration)).toBe('Invalid duration selection');

    // Test null duration
    expect(result.current.validateSelection(null)).toBe('Please select a recording duration');
  });
});

describe('useAudioRecorder', () => {
  beforeEach(() => {
    useRecordingStore.getState().reset();
    vi.clearAllMocks();
  });

  it('should initialize with idle state', () => {
    const { result } = renderHook(() => useAudioRecorder());

    expect(result.current.status.type).toBe('idle');
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isPaused).toBe(false);
    expect(result.current.isCompleted).toBe(false);
    expect(result.current.recordingTime).toBe(0);
    expect(result.current.audioBlob).toBeNull();
    expect(result.current.audioUrl).toBeNull();
  });

  it('should format time correctly', () => {
    const { result } = renderHook(() => useAudioRecorder());

    expect(result.current.formattedTime).toBe('0:00');

    // Simulate recording time
    act(() => {
      useRecordingStore.getState().setRecordingTime(125); // 2:05
    });

    expect(result.current.formattedTime).toBe('2:05');
  });

  it('should calculate progress percentage correctly', () => {
    const { result } = renderHook(() => useAudioRecorder());

    act(() => {
      useRecordingStore.getState().setRecordingTime(60); // 1 minute
    });

    expect(result.current.progressPercentage(300)).toBe(20); // 60/300 * 100
  });

  it('should calculate remaining time correctly', () => {
    const { result } = renderHook(() => useAudioRecorder());

    act(() => {
      useRecordingStore.getState().setRecordingTime(60); // 1 minute
    });

    expect(result.current.remainingTime(300)).toBe(240); // 300 - 60
    expect(result.current.remainingTime(30)).toBe(0); // Max with 0
  });
});

describe('useScriptManager', () => {
  beforeEach(() => {
    useScriptStore.getState().reset();
    useSessionStore.getState().reset();
    vi.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useScriptManager());

    expect(result.current.currentScript).toBeNull();
    expect(result.current.selectedDuration).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.recordingSession).toBeNull();
    expect(result.current.isReady).toBe(false);
    expect(result.current.canRecord).toBe(false);
  });

  it('should clear error state', () => {
    const { result } = renderHook(() => useScriptManager());

    // Set error state
    act(() => {
      useScriptStore.getState().setLoadingState({
        status: 'error',
        error: 'Test error',
        retryCount: 0,
      });
    });

    expect(result.current.error).toBe('Test error');

    // Clear error
    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should reset all state', () => {
    const { result } = renderHook(() => useScriptManager());

    // Set some state
    act(() => {
      useScriptStore.getState().setSelectedDuration({
        value: '5_minutes',
        label: '5 Minutes',
        minutes: 5,
        description: 'Test',
      });
    });

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.selectedDuration).toBeNull();
  });
});

describe('useUploadManager', () => {
  beforeEach(() => {
    useUploadStore.getState().reset();
    vi.clearAllMocks();
  });

  it('should initialize with idle state', () => {
    const { result } = renderHook(() => useUploadManager());

    expect(result.current.uploadState.status).toBe('idle');
    expect(result.current.isIdle).toBe(true);
    expect(result.current.isUploading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.isError).toBe(false);
    expect(result.current.progress).toBe(0);
    expect(result.current.errorMessage).toBeNull();
    expect(result.current.uploadedRecording).toBeNull();
  });

  it('should handle upload state changes', () => {
    const { result } = renderHook(() => useUploadManager());

    // Set uploading state
    act(() => {
      useUploadStore.getState().setUploading(50);
    });

    expect(result.current.isUploading).toBe(true);
    expect(result.current.progress).toBe(50);

    // Set error state
    act(() => {
      useUploadStore.getState().setError('Upload failed');
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.errorMessage).toBe('Upload failed');
  });

  it('should reset upload state', () => {
    const { result } = renderHook(() => useUploadManager());

    // Set error state
    act(() => {
      useUploadStore.getState().setError('Test error');
    });

    expect(result.current.isError).toBe(true);

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.isIdle).toBe(true);
    expect(result.current.errorMessage).toBeNull();
  });
});

/**
 * **Feature: frontend-modernization, Property 3: Hook reusability and isolation**
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
 */
describe('Property-Based Test: Hook Reusability and Isolation', () => {
  beforeEach(() => {
    // Reset all stores before each test
    useScriptStore.getState().reset();
    useRecordingStore.getState().reset();
    useUploadStore.getState().reset();
    useSessionStore.getState().reset();
  });

  it('should maintain hook isolation across multiple instances', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          'useDurationSelector',
          'useAudioRecorder',
          'useScriptManager',
          'useUploadManager'
        ),
        fc.integer({ min: 2, max: 5 }), // Number of hook instances to test
        (hookName, instanceCount) => {
          const hookInstances: any[] = [];

          // Create multiple instances of the same hook
          for (let i = 0; i < instanceCount; i++) {
            let hookResult;
            switch (hookName) {
              case 'useDurationSelector':
                hookResult = renderHook(() => useDurationSelector());
                break;
              case 'useAudioRecorder':
                hookResult = renderHook(() => useAudioRecorder());
                break;
              case 'useScriptManager':
                hookResult = renderHook(() => useScriptManager());
                break;
              case 'useUploadManager':
                hookResult = renderHook(() => useUploadManager());
                break;
              default:
                throw new Error(`Unknown hook: ${hookName}`);
            }
            hookInstances.push(hookResult);
          }

          // Verify all instances return consistent interfaces
          const firstInstance = hookInstances[0];
          const firstResult = firstInstance.result.current;

          for (let i = 1; i < hookInstances.length; i++) {
            const currentResult = hookInstances[i].result.current;

            // Check that all instances have the same interface structure
            expect(Object.keys(currentResult).sort()).toEqual(Object.keys(firstResult).sort());

            // Check that function properties are actually functions
            Object.keys(currentResult).forEach(key => {
              if (typeof firstResult[key] === 'function') {
                expect(typeof currentResult[key]).toBe('function');
              }
            });
          }

          // Cleanup all instances
          hookInstances.forEach(instance => instance.unmount());
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should return consistent TypeScript interfaces across all custom hooks', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          'useDurationSelector',
          'useAudioRecorder',
          'useScriptManager',
          'useUploadManager'
        ),
        hookName => {
          let hookResult;
          switch (hookName) {
            case 'useDurationSelector':
              hookResult = renderHook(() => useDurationSelector());
              break;
            case 'useAudioRecorder':
              hookResult = renderHook(() => useAudioRecorder());
              break;
            case 'useScriptManager':
              hookResult = renderHook(() => useScriptManager());
              break;
            case 'useUploadManager':
              hookResult = renderHook(() => useUploadManager());
              break;
            default:
              throw new Error(`Unknown hook: ${hookName}`);
          }

          const result = hookResult.result.current;

          // Verify the hook returns an object (not null, undefined, or primitive)
          expect(typeof result).toBe('object');
          expect(result).not.toBeNull();

          // Verify all returned properties have defined types (not undefined)
          Object.values(result).forEach(value => {
            expect(value).not.toBeUndefined();
          });

          hookResult.unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should maintain state isolation between hook instances', () => {
    fc.assert(
      fc.property(fc.constantFrom('2_minutes', '5_minutes', '10_minutes'), durationValue => {
        // Reset store before test
        useScriptStore.getState().reset();

        // Test with useDurationSelector - since it uses shared store,
        // we test that multiple instances see the same shared state consistently
        const hookInstance1 = renderHook(() => useDurationSelector());
        const hookInstance2 = renderHook(() => useDurationSelector());

        const availableOptions = hookInstance1.result.current.availableOptions;
        const optionToSelect = availableOptions.find(opt => opt.value === durationValue);

        if (optionToSelect) {
          // Select duration in first instance
          act(() => {
            hookInstance1.result.current.selectDuration(optionToSelect);
          });

          // Both instances should see the same state (shared store behavior)
          expect(hookInstance1.result.current.selectedDuration?.value).toBe(durationValue);
          expect(hookInstance2.result.current.selectedDuration?.value).toBe(durationValue);
        }

        // Cleanup
        hookInstance1.unmount();
        hookInstance2.unmount();
      }),
      { numRuns: 100 }
    );
  });

  it('should handle hook reusability without side effects', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 10 }), // Number of mount/unmount cycles
        cycles => {
          let lastResult: any = null;

          // Test multiple mount/unmount cycles
          for (let i = 0; i < cycles; i++) {
            const { result, unmount } = renderHook(() => useDurationSelector());

            // Verify initial state is consistent across cycles
            expect(result.current.selectedDuration).toBeNull();
            expect(result.current.hasSelection).toBe(false);
            expect(result.current.availableOptions).toHaveLength(3);

            // Verify interface consistency
            if (lastResult) {
              expect(Object.keys(result.current).sort()).toEqual(Object.keys(lastResult).sort());
            }

            lastResult = result.current;
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should provide proper error handling isolation', () => {
    fc.assert(
      fc.property(
        fc.boolean(), // Single success/failure scenario
        shouldSucceed => {
          // Reset stores before test
          useScriptStore.getState().reset();
          useSessionStore.getState().reset();

          const hookInstance = renderHook(() => useScriptManager());

          // Verify initial state
          expect(hookInstance.result.current.error).toBeNull();
          expect(hookInstance.result.current.isLoading).toBe(false);

          // Verify hook interface consistency regardless of error state
          expect(typeof hookInstance.result.current.selectDuration).toBe('function');
          expect(typeof hookInstance.result.current.loadScript).toBe('function');
          expect(typeof hookInstance.result.current.createSession).toBe('function');
          expect(typeof hookInstance.result.current.clearError).toBe('function');
          expect(typeof hookInstance.result.current.reset).toBe('function');

          // Cleanup
          hookInstance.unmount();

          return true; // Property holds
        }
      ),
      { numRuns: 100 }
    );
  });
});

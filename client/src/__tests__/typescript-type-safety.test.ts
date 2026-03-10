/**
 * **Feature: frontend-modernization, Property 5: TypeScript type safety enhancement**
 *
 * Property-based test to verify that enhanced TypeScript features provide
 * compile-time type safety and runtime validation for discriminated unions,
 * utility types, API responses, and event handlers.
 *
 * **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';

// Import types and utilities to test
import {
  RecordingStatus,
  UploadState,
  ScriptLoadingState,
  StrictDurationOption,
  ComponentProps,
  ButtonProps,
  StrictApiResponse,
  StrictApiError,
  ValidatedScript,
  ValidatedVoiceRecording,
  NetworkState,
  ExtractStatus,
  ExtractType,
  RequireFields,
  OptionalFields,
  DeepReadonly,
} from '../types/enhanced';

import {
  isValidRecordingStatus,
  isValidUploadState,
  isValidScriptLoadingState,
  isValidDurationOption,
  assertRecordingStatus,
  assertUploadState,
  assertScriptLoadingState,
  assertDurationOption,
  isApiSuccess,
  isApiError,
  validateApiResponse,
  createIdleNetworkState,
  createLoadingNetworkState,
  createSuccessNetworkState,
  createErrorNetworkState,
  transformLegacyRecordingState,
  transformLegacyUploadState,
} from '../utils/type-validation';

// ============================================================================
// PROPERTY-BASED TEST GENERATORS
// ============================================================================

// Generator for RecordingStatus discriminated union
const recordingStatusArbitrary = fc.oneof(
  fc.constant({ type: 'idle' as const }),
  fc.record({
    type: fc.constant('initializing' as const),
    message: fc.string({ minLength: 1 }),
  }),
  fc.record({
    type: fc.constant('recording' as const),
    startTime: fc.integer({ min: 0 }),
    duration: fc.integer({ min: 0 }),
  }),
  fc.record({
    type: fc.constant('paused' as const),
    pausedAt: fc.integer({ min: 0 }),
    totalDuration: fc.integer({ min: 0 }),
  }),
  fc.record({
    type: fc.constant('completed' as const),
    blob: fc.constant(new Blob(['test'], { type: 'audio/webm' })),
    duration: fc.integer({ min: 1 }),
    url: fc.webUrl(),
  }),
  fc.record({
    type: fc.constant('error' as const),
    error: fc.string({ minLength: 1 }),
    code: fc.option(fc.string({ minLength: 1 })),
  })
);

// Generator for UploadState discriminated union
const uploadStateArbitrary = fc.oneof(
  fc.constant({ status: 'idle' as const }),
  fc.record({
    status: fc.constant('preparing' as const),
    message: fc.string({ minLength: 1 }),
  }),
  fc.record({
    status: fc.constant('uploading' as const),
    progress: fc.integer({ min: 0, max: 100 }),
    bytesUploaded: fc.integer({ min: 0 }),
    totalBytes: fc.integer({ min: 1 }),
  }),
  fc.record({
    status: fc.constant('processing' as const),
    message: fc.string({ minLength: 1 }),
  }),
  fc.record({
    status: fc.constant('success' as const),
    recording: fc.record({
      id: fc.integer({ min: 1 }),
      user_id: fc.integer({ min: 1 }),
      script_id: fc.integer({ min: 1 }),
      language_id: fc.integer({ min: 1 }),
      file_path: fc.string({ minLength: 1 }),
      duration: fc.integer({ min: 1 }),
      status: fc.constantFrom('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED'),
      meta_data: fc.record({
        file_size: fc.integer({ min: 1 }),
        sample_rate: fc.integer({ min: 8000 }),
        channels: fc.integer({ min: 1, max: 2 }),
        bit_depth: fc.integer({ min: 16 }),
        format: fc.string({ minLength: 1 }),
      }),
      created_at: fc
        .integer({ min: 1577836800000, max: 1924992000000 })
        .map(ts => new Date(ts).toISOString()),
      updated_at: fc
        .integer({ min: 1577836800000, max: 1924992000000 })
        .map(ts => new Date(ts).toISOString()),
    }),
    uploadTime: fc.integer({ min: 0 }),
  }),
  fc.record({
    status: fc.constant('error' as const),
    error: fc.string({ minLength: 1 }),
    code: fc.option(fc.string({ minLength: 1 })),
    retryable: fc.boolean(),
  })
);

// Generator for ScriptLoadingState discriminated union
const scriptLoadingStateArbitrary = fc.oneof(
  fc.constant({ status: 'idle' as const }),
  fc.record({
    status: fc.constant('loading' as const),
    duration: fc.constantFrom('2_minutes', '5_minutes', '10_minutes'),
  }),
  fc.record({
    status: fc.constant('loaded' as const),
    script: fc.record({
      id: fc.integer({ min: 1 }),
      text: fc.string({ minLength: 10 }),
      duration_category: fc.constantFrom('2_minutes', '5_minutes', '10_minutes'),
      language_id: fc.integer({ min: 1 }),
      meta_data: fc.record({
        word_count: fc.integer({ min: 1 }),
        estimated_duration: fc.integer({ min: 1 }),
        difficulty_level: fc.constantFrom('easy', 'medium', 'hard'),
        tags: fc.array(fc.string({ minLength: 1 })),
      }),
      created_at: fc
        .integer({ min: 1577836800000, max: 1924992000000 })
        .map(ts => new Date(ts).toISOString()),
      updated_at: fc
        .integer({ min: 1577836800000, max: 1924992000000 })
        .map(ts => new Date(ts).toISOString()),
    }),
    loadTime: fc.integer({ min: 0 }),
  }),
  fc.record({
    status: fc.constant('error' as const),
    error: fc.string({ minLength: 1 }),
    retryCount: fc.integer({ min: 0 }),
  })
);

// Generator for StrictDurationOption
const durationOptionArbitrary = fc.record({
  value: fc.constantFrom('2_minutes', '5_minutes', '10_minutes'),
  label: fc.string({ minLength: 1 }),
  minutes: fc.constantFrom(2, 5, 10),
  description: fc.string({ minLength: 1 }),
  maxFileSize: fc.integer({ min: 1024 }),
  recommendedFor: fc.array(fc.string({ minLength: 1 })),
});

// Generator for API responses
const apiSuccessArbitrary = <T>(dataArb: fc.Arbitrary<T>) =>
  fc.record({
    data: dataArb,
    success: fc.constant(true as const),
    message: fc.option(fc.string({ minLength: 1 })),
    timestamp: fc
      .integer({ min: 1577836800000, max: 1924992000000 })
      .map(ts => new Date(ts).toISOString()),
    requestId: fc.string({ minLength: 1 }),
  });

const apiErrorArbitrary = fc.record({
  success: fc.constant(false as const),
  error: fc.record({
    message: fc.string({ minLength: 1 }),
    code: fc.string({ minLength: 1 }),
    statusCode: fc.integer({ min: 400, max: 599 }),
    details: fc.option(fc.record({})),
  }),
  timestamp: fc
    .integer({ min: 1577836800000, max: 1924992000000 })
    .map(ts => new Date(ts).toISOString()),
  requestId: fc.string({ minLength: 1 }),
});

// Generator for invalid data (for negative testing)
const invalidDataArbitrary = fc.oneof(
  fc.constant(null),
  fc.constant(undefined),
  fc.string(),
  fc.integer(),
  fc.boolean(),
  fc.array(fc.anything()),
  fc.record({
    invalidField: fc.anything(),
  })
);

// ============================================================================
// PROPERTY-BASED TESTS
// ============================================================================

describe('TypeScript Type Safety Enhancement Property Tests', () => {
  /**
   * Property 5.1: Discriminated unions provide type safety
   * For any valid discriminated union value, type guards should correctly identify the variant
   */
  describe('Discriminated Union Type Safety', () => {
    it('should correctly validate RecordingStatus discriminated unions', () => {
      fc.assert(
        fc.property(recordingStatusArbitrary, status => {
          // Valid status should pass validation
          expect(isValidRecordingStatus(status)).toBe(true);

          // Should not throw when asserting valid status
          expect(() => assertRecordingStatus(status)).not.toThrow();

          // Assertion should return the same value
          const asserted = assertRecordingStatus(status);
          expect(asserted).toEqual(status);

          // Type narrowing should work correctly based on discriminant
          if (status.type === 'recording') {
            expect(typeof status.startTime).toBe('number');
            expect(typeof status.duration).toBe('number');
          } else if (status.type === 'completed') {
            expect(status.blob).toBeInstanceOf(Blob);
            expect(typeof status.duration).toBe('number');
            expect(typeof status.url).toBe('string');
          } else if (status.type === 'error') {
            expect(typeof status.error).toBe('string');
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly validate UploadState discriminated unions', () => {
      fc.assert(
        fc.property(uploadStateArbitrary, state => {
          // Valid state should pass validation
          expect(isValidUploadState(state)).toBe(true);

          // Should not throw when asserting valid state
          expect(() => assertUploadState(state)).not.toThrow();

          // Assertion should return the same value
          const asserted = assertUploadState(state);
          expect(asserted).toEqual(state);

          // Type narrowing should work correctly based on discriminant
          if (state.status === 'uploading') {
            expect(typeof state.progress).toBe('number');
            expect(state.progress).toBeGreaterThanOrEqual(0);
            expect(state.progress).toBeLessThanOrEqual(100);
          } else if (state.status === 'success') {
            expect(typeof state.recording).toBe('object');
            expect(state.recording).not.toBeNull();
            expect(typeof state.uploadTime).toBe('number');
          } else if (state.status === 'error') {
            expect(typeof state.error).toBe('string');
            expect(typeof state.retryable).toBe('boolean');
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly validate ScriptLoadingState discriminated unions', () => {
      fc.assert(
        fc.property(scriptLoadingStateArbitrary, state => {
          // Valid state should pass validation
          expect(isValidScriptLoadingState(state)).toBe(true);

          // Should not throw when asserting valid state
          expect(() => assertScriptLoadingState(state)).not.toThrow();

          // Assertion should return the same value
          const asserted = assertScriptLoadingState(state);
          expect(asserted).toEqual(state);

          // Type narrowing should work correctly based on discriminant
          if (state.status === 'loaded') {
            expect(typeof state.script).toBe('object');
            expect(state.script).not.toBeNull();
            expect(typeof state.loadTime).toBe('number');
          } else if (state.status === 'error') {
            expect(typeof state.error).toBe('string');
            expect(typeof state.retryCount).toBe('number');
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should reject invalid discriminated union values', () => {
      fc.assert(
        fc.property(invalidDataArbitrary, invalidData => {
          // Invalid data should fail validation
          expect(isValidRecordingStatus(invalidData)).toBe(false);
          expect(isValidUploadState(invalidData)).toBe(false);
          expect(isValidScriptLoadingState(invalidData)).toBe(false);

          // Assertions should throw for invalid data
          expect(() => assertRecordingStatus(invalidData)).toThrow();
          expect(() => assertUploadState(invalidData)).toThrow();
          expect(() => assertScriptLoadingState(invalidData)).toThrow();
        }),
        { numRuns: 50 }
      );
    });
  });

  /**
   * Property 5.2: Utility types work correctly for state transformations
   * For any valid data, utility type transformations should preserve type safety
   */
  describe('Utility Type Transformations', () => {
    it('should correctly validate StrictDurationOption utility type', () => {
      fc.assert(
        fc.property(durationOptionArbitrary, option => {
          // Valid option should pass validation
          expect(isValidDurationOption(option)).toBe(true);

          // Should not throw when asserting valid option
          expect(() => assertDurationOption(option)).not.toThrow();

          // Assertion should return the same value
          const asserted = assertDurationOption(option);
          expect(asserted).toEqual(option);

          // Type constraints should be enforced
          expect(['2_minutes', '5_minutes', '10_minutes']).toContain(option.value);
          expect([2, 5, 10]).toContain(option.minutes);
          expect(Array.isArray(option.recommendedFor)).toBe(true);
          expect(option.recommendedFor.every(item => typeof item === 'string')).toBe(true);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform legacy states to new discriminated unions', () => {
      fc.assert(
        fc.property(
          fc.record({
            isRecording: fc.boolean(),
            isPaused: fc.boolean(),
            recordingTime: fc.integer({ min: 0 }),
            audioBlob: fc.option(fc.constant(new Blob(['test'], { type: 'audio/webm' }))),
            audioUrl: fc.option(fc.webUrl()),
          }),
          legacyState => {
            const transformed = transformLegacyRecordingState(legacyState);

            // Transformed state should be valid
            expect(isValidRecordingStatus(transformed)).toBe(true);

            // Transformation logic should be consistent
            if (legacyState.audioBlob && legacyState.audioUrl) {
              expect(transformed.type).toBe('completed');
              if (transformed.type === 'completed') {
                expect(transformed.blob).toBe(legacyState.audioBlob);
                expect(transformed.url).toBe(legacyState.audioUrl);
              }
            } else if (legacyState.isRecording) {
              if (legacyState.isPaused) {
                expect(transformed.type).toBe('paused');
              } else {
                expect(transformed.type).toBe('recording');
              }
            } else {
              expect(transformed.type).toBe('idle');
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 5.3: API response types provide strict validation
   * For any API response, type guards should correctly identify success/error states
   */
  describe('Strict API Response Validation', () => {
    it('should correctly validate successful API responses', () => {
      fc.assert(
        fc.property(apiSuccessArbitrary(fc.record({ test: fc.string() })), response => {
          // Valid success response should pass validation
          expect(isApiSuccess(response)).toBe(true);
          expect(isApiError(response)).toBe(false);

          // Should have required fields
          expect(response.success).toBe(true);
          expect(response.data).toBeDefined();
          expect(typeof response.timestamp).toBe('string');
          expect(typeof response.requestId).toBe('string');

          // Validation function should work correctly
          const validated = validateApiResponse(response);
          expect(validated).toEqual(response);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly validate API error responses', () => {
      fc.assert(
        fc.property(apiErrorArbitrary, response => {
          // Valid error response should pass validation
          expect(isApiError(response)).toBe(true);
          expect(isApiSuccess(response)).toBe(false);

          // Should have required error fields
          expect(response.success).toBe(false);
          expect(typeof response.error.message).toBe('string');
          expect(typeof response.error.code).toBe('string');
          expect(typeof response.error.statusCode).toBe('number');
          expect(response.error.statusCode).toBeGreaterThanOrEqual(400);
          expect(response.error.statusCode).toBeLessThan(600);

          // Validation function should return error as-is
          const validated = validateApiResponse(response);
          expect(validated).toEqual(response);
        }),
        { numRuns: 100 }
      );
    });

    it('should reject invalid API responses', () => {
      fc.assert(
        fc.property(invalidDataArbitrary, invalidResponse => {
          // Invalid responses should fail validation
          expect(isApiSuccess(invalidResponse)).toBe(false);
          expect(isApiError(invalidResponse)).toBe(false);

          // Validation should throw for invalid responses
          expect(() => validateApiResponse(invalidResponse)).toThrow();
        }),
        { numRuns: 50 }
      );
    });
  });

  /**
   * Property 5.4: Network state utilities maintain type safety
   * For any network state operation, type safety should be preserved
   */
  describe('Network State Type Safety', () => {
    it('should create correctly typed network states', () => {
      fc.assert(
        fc.property(
          fc.record({ test: fc.string() }),
          fc.string({ minLength: 1 }),
          fc.integer({ min: 400, max: 599 }),
          (testData, errorMessage, statusCode) => {
            // Idle state
            const idleState = createIdleNetworkState<typeof testData>();
            expect(idleState.status).toBe('idle');
            expect(Object.keys(idleState)).toEqual(['status']);

            // Loading state
            const loadingState = createLoadingNetworkState<typeof testData>();
            expect(loadingState.status).toBe('loading');

            // Success state
            const successState = createSuccessNetworkState(testData);
            expect(successState.status).toBe('success');
            if (successState.status === 'success') {
              expect(successState.data).toEqual(testData);
              expect(typeof successState.timestamp).toBe('number');
            }

            // Error state
            const errorState = createErrorNetworkState<typeof testData>(errorMessage, statusCode);
            expect(errorState.status).toBe('error');
            if (errorState.status === 'error') {
              expect(errorState.error).toBe(errorMessage);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 5.5: Component props maintain strict typing
   * For any component props, TypeScript constraints should be enforced
   */
  describe('Component Props Type Safety', () => {
    it('should enforce ComponentProps base interface', () => {
      fc.assert(
        fc.property(
          fc.record({
            className: fc.option(fc.string(), { nil: undefined }),
            'data-testid': fc.option(fc.string(), { nil: undefined }),
            id: fc.option(fc.string(), { nil: undefined }),
            customProp: fc.string(),
          }),
          props => {
            // ComponentProps should allow base props plus custom props
            const componentProps: ComponentProps<{ customProp: string }> = props;

            // Base props should be optional
            expect(componentProps.customProp).toBeDefined();

            // Type system should enforce correct types
            if (componentProps.className !== undefined) {
              expect(typeof componentProps.className).toBe('string');
            }
            if (componentProps['data-testid'] !== undefined) {
              expect(typeof componentProps['data-testid']).toBe('string');
            }
            if (componentProps.id !== undefined) {
              expect(typeof componentProps.id).toBe('string');
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should enforce ButtonProps constraints', () => {
      fc.assert(
        fc.property(
          fc.record({
            variant: fc.option(
              fc.constantFrom('primary', 'secondary', 'destructive', 'success', 'warning'),
              { nil: undefined }
            ),
            size: fc.option(fc.constantFrom('sm', 'md', 'lg'), { nil: undefined }),
            disabled: fc.option(fc.boolean(), { nil: undefined }),
            loading: fc.option(fc.boolean(), { nil: undefined }),
            type: fc.option(fc.constantFrom('button', 'submit', 'reset'), { nil: undefined }),
            children: fc.constant('Test Button'),
            className: fc.option(fc.string(), { nil: undefined }),
          }),
          props => {
            // ButtonProps should enforce correct variant and size types
            const buttonProps: ButtonProps = props;

            // Required children prop
            expect(buttonProps.children).toBeDefined();

            // Optional props should have correct types when present
            if (buttonProps.variant !== undefined) {
              expect(['primary', 'secondary', 'destructive', 'success', 'warning']).toContain(
                buttonProps.variant
              );
            }
            if (buttonProps.size !== undefined) {
              expect(['sm', 'md', 'lg']).toContain(buttonProps.size);
            }
            if (buttonProps.type !== undefined) {
              expect(['button', 'submit', 'reset']).toContain(buttonProps.type);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Comprehensive property: All enhanced TypeScript features work together
   * For any combination of enhanced types, the system should maintain type safety
   */
  describe('Comprehensive Type Safety Integration', () => {
    it('should maintain type safety across all enhanced features', () => {
      fc.assert(
        fc.property(
          recordingStatusArbitrary,
          uploadStateArbitrary,
          scriptLoadingStateArbitrary,
          durationOptionArbitrary,
          (recordingStatus, uploadState, scriptState, durationOption) => {
            // All discriminated unions should validate correctly
            expect(isValidRecordingStatus(recordingStatus)).toBe(true);
            expect(isValidUploadState(uploadState)).toBe(true);
            expect(isValidScriptLoadingState(scriptState)).toBe(true);
            expect(isValidDurationOption(durationOption)).toBe(true);

            // Type assertions should work without throwing
            expect(() => {
              assertRecordingStatus(recordingStatus);
              assertUploadState(uploadState);
              assertScriptLoadingState(scriptState);
              assertDurationOption(durationOption);
            }).not.toThrow();

            // Network states should work with any data type
            const networkState = createSuccessNetworkState({
              recording: recordingStatus,
              upload: uploadState,
              script: scriptState,
              duration: durationOption,
            });

            expect(networkState.status).toBe('success');
            if (networkState.status === 'success') {
              expect(networkState.data.recording).toEqual(recordingStatus);
              expect(networkState.data.upload).toEqual(uploadState);
              expect(networkState.data.script).toEqual(scriptState);
              expect(networkState.data.duration).toEqual(durationOption);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

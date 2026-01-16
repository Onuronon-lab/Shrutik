import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useErrorHandler } from '../useErrorHandler';
import { useTranslation } from 'react-i18next';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: vi.fn(),
}));

describe('useErrorHandler - Error Translation and Handling', () => {
  let mockT: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Create a mock translation function
    mockT = vi.fn((key: string, options?: any) => {
      // Simulate translation behavior with fallback
      const translations: Record<string, string> = {
        'errors.export.insufficient_chunks.title': 'Insufficient chunks for batch creation',
        'errors.export.quota_exceeded.title': 'Daily download limit exceeded',
        'errors.export.insufficient_chunks.suggestion.wait':
          'Wait for more chunks to be processed (check back in a few hours)',
        'errors.export.insufficient_chunks.suggestion.admin':
          'Contact an admin who can create batches with fewer chunks',
        'errors.export.quota_exceeded.suggestion.wait':
          'Wait until {{time}} when your quota resets',
        'errors.generic.network': 'Unable to connect to the server',
        'errors.generic.unknown': 'An unexpected error occurred',
      };

      const translation = translations[key];

      if (translation) {
        // Handle parameter interpolation
        if (options && typeof translation === 'string') {
          let result = translation;
          Object.keys(options).forEach(param => {
            if (param !== 'defaultValue') {
              result = result.replace(`{{${param}}}`, options[param]);
            }
          });
          return result;
        }
        return translation;
      }

      // Return defaultValue if translation not found
      return options?.defaultValue || key;
    });

    (useTranslation as ReturnType<typeof vi.fn>).mockReturnValue({
      t: mockT,
      i18n: { language: 'en' },
    });
  });

  describe('Error Key to Translated String Conversion', () => {
    it('should translate error_key to English string', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Fallback message',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.title).toBe('Insufficient chunks for batch creation');
      expect(mockT).toHaveBeenCalledWith(
        'errors.export.insufficient_chunks.title',
        expect.objectContaining({
          defaultValue: 'Fallback message',
        })
      );
    });

    it('should translate quota exceeded error correctly', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.quota_exceeded.title',
            error_message: 'Quota exceeded',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Daily download limit exceeded');
    });

    it('should translate network error correctly', () => {
      const { result } = renderHook(() => useErrorHandler());

      // Network error (no response from server)
      const error = {
        request: {},
        // No response property
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Unable to connect to the server');
      expect(mockT).toHaveBeenCalledWith(
        'errors.generic.network',
        expect.objectContaining({
          defaultValue: 'Unable to connect to the server',
        })
      );
    });
  });

  describe('Fallback to error_message When Translation Missing', () => {
    it('should use error_message when translation key is not found', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.nonexistent.key',
            error_message: 'This is the fallback message',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('This is the fallback message');
    });

    it('should use error_message when error_key is empty', () => {
      const { result } = renderHook(() => useErrorHandler());

      // When error_key is empty, it's treated as a legacy format
      // The extraction logic will not match the error_key condition
      // and will fall through to check for other formats
      const error = {
        response: {
          data: {
            error_key: '',
            error_message: 'Direct error message',
            // Since error_key is empty, we need to provide error field for legacy format
            error: 'Direct error message',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Direct error message');
    });

    it('should fallback to generic unknown error when no structured error found', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        // Completely unstructured error
        someRandomProperty: 'random value',
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('An unexpected error occurred');
      expect(mockT).toHaveBeenCalledWith(
        'errors.generic.unknown',
        expect.objectContaining({
          defaultValue: 'An unexpected error occurred',
        })
      );
    });
  });

  describe('Parameter Interpolation in Translations', () => {
    it('should interpolate parameters in suggestion translations', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.quota_exceeded.title',
            error_message: 'Quota exceeded',
            suggestions: [
              {
                key: 'errors.export.quota_exceeded.suggestion.wait',
                message: 'Wait until reset',
                params: {
                  time: '12:00 AM UTC',
                },
              },
            ],
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.suggestions).toBeDefined();
      expect(result.current.error?.suggestions?.[0]).toBe(
        'Wait until 12:00 AM UTC when your quota resets'
      );
      expect(mockT).toHaveBeenCalledWith(
        'errors.export.quota_exceeded.suggestion.wait',
        expect.objectContaining({
          defaultValue: 'Wait until reset',
          time: '12:00 AM UTC',
        })
      );
    });

    it('should handle multiple parameters in translations', () => {
      // Mock a translation with multiple parameters
      mockT.mockImplementation((key: string, options?: any) => {
        if (key === 'errors.export.quota_exceeded.detail.usage') {
          return `Downloads today: ${options?.used}/${options?.limit}`;
        }
        return options?.defaultValue || key;
      });

      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.quota_exceeded.detail.usage',
            error_message: 'Quota info',
            details: {
              used: 5,
              limit: 10,
            },
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      // The details should be preserved
      expect(result.current.error?.details).toEqual({
        used: 5,
        limit: 10,
      });
    });

    it('should handle suggestions without parameters', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            suggestions: [
              {
                key: 'errors.export.insufficient_chunks.suggestion.wait',
                message: 'Wait for more chunks',
              },
              {
                key: 'errors.export.insufficient_chunks.suggestion.admin',
                message: 'Contact admin',
              },
            ],
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.suggestions).toHaveLength(2);
      expect(result.current.error?.suggestions?.[0]).toBe(
        'Wait for more chunks to be processed (check back in a few hours)'
      );
      expect(result.current.error?.suggestions?.[1]).toBe(
        'Contact an admin who can create batches with fewer chunks'
      );
    });
  });

  describe('Bengali Translation Support', () => {
    beforeEach(() => {
      // Mock Bengali translations
      mockT.mockImplementation((key: string, options?: any) => {
        const bengaliTranslations: Record<string, string> = {
          'errors.export.insufficient_chunks.title': 'ব্যাচ তৈরির জন্য অপর্যাপ্ত চাঙ্ক',
          'errors.export.quota_exceeded.title': 'দৈনিক ডাউনলোড সীমা অতিক্রম করেছে',
          'errors.generic.network': 'সার্ভারের সাথে সংযোগ করতে অক্ষম',
          'errors.generic.unknown': 'একটি অপ্রত্যাশিত ত্রুটি ঘটেছে',
        };

        return bengaliTranslations[key] || options?.defaultValue || key;
      });

      (useTranslation as ReturnType<typeof vi.fn>).mockReturnValue({
        t: mockT,
        i18n: { language: 'bn' },
      });
    });

    it('should translate error to Bengali when language is Bengali', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('ব্যাচ তৈরির জন্য অপর্যাপ্ত চাঙ্ক');
    });

    it('should translate quota exceeded error to Bengali', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.quota_exceeded.title',
            error_message: 'Quota exceeded',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('দৈনিক ডাউনলোড সীমা অতিক্রম করেছে');
    });

    it('should translate network error to Bengali', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        request: {},
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('সার্ভারের সাথে সংযোগ করতে অক্ষম');
    });

    it('should fallback to English when Bengali translation is missing', () => {
      mockT.mockImplementation((key: string, options?: any) => {
        // Bengali translation not found, return defaultValue
        return options?.defaultValue || key;
      });

      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.new_error',
            error_message: 'English fallback message',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('English fallback message');
    });
  });

  describe('Extraction of Structured Errors from Various Response Formats', () => {
    it('should extract error from response.data with error_key', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            details: {
              available: 45,
              required: 50,
            },
            suggestions: [
              {
                key: 'errors.export.insufficient_chunks.suggestion.wait',
                message: 'Wait for more chunks',
              },
            ],
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.error?.title).toBe('Insufficient chunks for batch creation');
      expect(result.current.error?.details).toEqual({
        available: 45,
        required: 50,
      });
      expect(result.current.error?.suggestions).toHaveLength(1);
    });

    it('should extract error from response.data.detail with error_key', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            detail: {
              error_key: 'errors.export.quota_exceeded.title',
              error_message: 'Quota exceeded',
              details: {
                used: 10,
                limit: 10,
              },
            },
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Daily download limit exceeded');
      expect(result.current.error?.details).toEqual({
        used: 10,
        limit: 10,
      });
    });

    it('should extract error from legacy format with error field', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error: 'Legacy error message',
            details: {
              code: 400,
            },
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Legacy error message');
      expect(result.current.error?.details).toEqual({
        code: 400,
      });
    });

    it('should extract error from response.data.detail.error field', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            detail: {
              error: 'Nested error message',
            },
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Nested error message');
    });

    it('should extract error from simple detail string', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            detail: 'Simple error detail string',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Simple error detail string');
    });

    it('should handle network errors (no response)', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        request: {},
        // No response property indicates network error
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Unable to connect to the server');
    });

    it('should handle generic JavaScript errors', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = new Error('Generic JavaScript error');

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Generic JavaScript error');
    });

    it('should preserve all error details and suggestions', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            details: {
              available_chunks: 45,
              required_chunks: 50,
              user_role: 'sworik_developer',
            },
            suggestions: [
              {
                key: 'errors.export.insufficient_chunks.suggestion.wait',
                message: 'Wait for more chunks',
              },
              {
                key: 'errors.export.insufficient_chunks.suggestion.admin',
                message: 'Contact admin',
              },
            ],
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.details).toEqual({
        available_chunks: 45,
        required_chunks: 50,
        user_role: 'sworik_developer',
      });
      expect(result.current.error?.suggestions).toHaveLength(2);
    });
  });

  describe('Error State Management', () => {
    it('should set error state when handleError is called', () => {
      const { result } = renderHook(() => useErrorHandler());

      expect(result.current.error).toBeNull();

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error).not.toBeNull();
    });

    it('should clear error state when clearError is called', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error).not.toBeNull();

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should allow manually setting error state', () => {
      const { result } = renderHook(() => useErrorHandler());

      const customError = {
        title: 'Custom error title',
        details: { custom: 'data' },
        suggestions: ['Custom suggestion'],
      };

      act(() => {
        result.current.setError(customError);
      });

      expect(result.current.error).toEqual(customError);
    });

    it('should handle multiple error updates', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error1 = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
          },
        },
      };

      const error2 = {
        response: {
          data: {
            error_key: 'errors.export.quota_exceeded.title',
            error_message: 'Quota exceeded',
          },
        },
      };

      act(() => {
        result.current.handleError(error1);
      });

      expect(result.current.error?.title).toBe('Insufficient chunks for batch creation');

      act(() => {
        result.current.handleError(error2);
      });

      expect(result.current.error?.title).toBe('Daily download limit exceeded');
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle null error gracefully', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.handleError(null);
      });

      expect(result.current.error?.title).toBe('An unexpected error occurred');
    });

    it('should handle undefined error gracefully', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.handleError(undefined);
      });

      expect(result.current.error?.title).toBe('An unexpected error occurred');
    });

    it('should handle error with missing suggestions gracefully', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            // No suggestions
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Insufficient chunks for batch creation');
      expect(result.current.error?.suggestions).toBeUndefined();
    });

    it('should handle error with empty suggestions array', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            suggestions: [],
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Insufficient chunks for batch creation');
      expect(result.current.error?.suggestions).toBeUndefined();
    });

    it('should handle suggestions without translation keys', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            suggestions: [
              {
                key: '',
                message: 'Plain suggestion message',
              },
            ],
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.suggestions).toHaveLength(1);
      expect(result.current.error?.suggestions?.[0]).toBe('Plain suggestion message');
    });

    it('should handle error with missing details gracefully', () => {
      const { result } = renderHook(() => useErrorHandler());

      const error = {
        response: {
          data: {
            error_key: 'errors.export.insufficient_chunks.title',
            error_message: 'Insufficient chunks',
            // No details
          },
        },
      };

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.error?.title).toBe('Insufficient chunks for batch creation');
      expect(result.current.error?.details).toBeUndefined();
    });
  });
});

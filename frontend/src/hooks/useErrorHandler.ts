import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { StructuredError, TranslatedError, ErrorSuggestion } from '../types/errors';

interface UseErrorHandlerReturn {
  error: TranslatedError | null;
  setError: (error: TranslatedError | null) => void;
  clearError: () => void;
  handleError: (error: any) => void;
}

/**
 * Custom hook for handling and translating errors throughout the application
 *
 * This hook processes errors from various sources (API responses, network errors, etc.),
 * extracts structured error information, translates error messages using i18n,
 * and provides a consistent error interface for display components.
 *
 * @returns {UseErrorHandlerReturn} Object containing error state and handler functions
 *
 * @example
 * const { error, handleError, clearError } = useErrorHandler();
 *
 * try {
 *   await apiCall();
 * } catch (err) {
 *   handleError(err);
 * }
 */
export function useErrorHandler(): UseErrorHandlerReturn {
  const { t } = useTranslation();
  const [error, setErrorState] = useState<TranslatedError | null>(null);

  const setError = useCallback((error: TranslatedError | null) => {
    setErrorState(error);
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  /**
   * Extracts a structured error from various error response formats
   *
   * Handles multiple error response formats from the backend:
   * - error_key-based structured errors (new format)
   * - Legacy error formats with error/detail fields
   * - Network errors
   * - Generic JavaScript errors
   *
   * @param {any} error - The error object to extract from
   * @returns {StructuredError | null} Structured error or null if extraction fails
   */
  const extractStructuredError = useCallback((error: any): StructuredError | null => {
    // FastAPI format: error_key in detail object (most common for our backend)
    if (
      error?.response?.data?.detail &&
      typeof error.response.data.detail === 'object' &&
      !Array.isArray(error.response.data.detail)
    ) {
      const detail = error.response.data.detail;
      if (detail.error_key) {
        return {
          error_key: detail.error_key,
          error_message: detail.error_message || 'An error occurred',
          details: detail.details,
          suggestions: detail.suggestions,
        };
      }
    }

    // New format: error_key-based structured error directly in response.data
    if (error?.response?.data?.error_key) {
      return {
        error_key: error.response.data.error_key,
        error_message: error.response.data.error_message || 'An error occurred',
        details: error.response.data.details,
        suggestions: error.response.data.suggestions,
      };
    }

    // Legacy format: error field with details in response.data
    if (error?.response?.data?.error && typeof error.response.data.error === 'string') {
      return {
        error_key: '', // No error_key in legacy format
        error_message: error.response.data.error,
        details: error.response.data.details,
        suggestions: error.response.data.suggestions,
      };
    }

    // Legacy format: error field in detail object
    if (
      error?.response?.data?.detail?.error &&
      typeof error.response.data.detail.error === 'string'
    ) {
      return {
        error_key: '',
        error_message: error.response.data.detail.error,
        details: error.response.data.detail.details,
        suggestions: error.response.data.detail.suggestions,
      };
    }

    // Simple detail string
    if (error?.response?.data?.detail && typeof error.response.data.detail === 'string') {
      return {
        error_key: '',
        error_message: error.response.data.detail,
      };
    }

    // Network error (no response from server)
    if (error?.request && !error?.response) {
      return {
        error_key: 'errors.generic.network',
        error_message: 'Unable to connect to the server',
      };
    }

    // Generic JavaScript error
    if (error?.message) {
      return {
        error_key: '',
        error_message: error.message,
      };
    }

    return null;
  }, []);

  /**
   * Translates a structured error into a user-facing translated error
   *
   * Converts error_key-based errors into translated strings using i18n.
   * Falls back to error_message if translation is not available.
   * Translates all suggestions and preserves error details.
   *
   * @param {StructuredError} structuredError - The structured error to translate
   * @returns {TranslatedError} Translated error ready for display
   */
  const translateError = useCallback(
    (structuredError: StructuredError): TranslatedError => {
      // Translate error title using error_key, fallback to error_message
      const title = structuredError.error_key
        ? t(structuredError.error_key, {
            defaultValue: structuredError.error_message,
          })
        : structuredError.error_message;

      // Translate suggestions if present
      const suggestions = structuredError.suggestions?.map((suggestion: ErrorSuggestion) => {
        if (suggestion.key) {
          return t(suggestion.key, {
            defaultValue: suggestion.message,
            ...suggestion.params,
          });
        }
        return suggestion.message;
      });

      const translatedError: TranslatedError = {
        title,
      };

      if (structuredError.details) {
        translatedError.details = structuredError.details;
      }

      if (suggestions && suggestions.length > 0) {
        translatedError.suggestions = suggestions;
      }

      return translatedError;
    },
    [t]
  );

  /**
   * Handles errors from any source and converts them to translated errors
   *
   * Main error handling function that:
   * 1. Extracts structured error information
   * 2. Translates error messages and suggestions
   * 3. Updates error state for display
   *
   * @param {any} error - The error to handle (can be from API, network, etc.)
   */
  const handleError = useCallback(
    (error: any) => {
      const structuredError = extractStructuredError(error);

      if (structuredError) {
        const translatedError = translateError(structuredError);
        setErrorState(translatedError);
      } else {
        // Fallback for completely unstructured errors
        setErrorState({
          title: t('errors.generic.unknown', {
            defaultValue: 'An unexpected error occurred',
          }),
        });
      }
    },
    [extractStructuredError, translateError, t]
  );

  return { error, setError, clearError, handleError };
}

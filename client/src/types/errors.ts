/**
 * Error type definitions for structured error handling and translation
 *
 * This module provides TypeScript interfaces for handling errors throughout
 * the application with support for internationalization (i18n) and structured
 * error information.
 */

/**
 * Represents a suggestion for resolving an error
 *
 * @interface ErrorSuggestion
 * @property {string} key - Translation key for the suggestion message (e.g., "errors.export.insufficient_chunks.suggestion.wait")
 * @property {string} message - Fallback message in English if translation is not available
 * @property {Record<string, any>} [params] - Optional parameters for interpolation in translated messages (e.g., {count: 5, time: "2:00 PM"})
 *
 * @example
 * {
 *   key: "errors.export.insufficient_chunks.suggestion.wait",
 *   message: "Wait for more chunks to be processed",
 *   params: { hours: 2 }
 * }
 */
export interface ErrorSuggestion {
  key: string;
  message: string;
  params?: Record<string, any>;
}

/**
 * Represents a structured error response from the backend API
 *
 * This interface defines the format of error responses that include
 * translation keys, fallback messages, contextual details, and actionable
 * suggestions for error resolution.
 *
 * @interface StructuredError
 * @property {string} error_key - Translation key for the error message (e.g., "errors.export.insufficient_chunks")
 * @property {string} error_message - Fallback error message in English if translation is not available
 * @property {Record<string, any>} [details] - Optional contextual information about the error (e.g., available_chunks, required_chunks, quota_status)
 * @property {ErrorSuggestion[]} [suggestions] - Optional array of suggestions for resolving the error
 *
 * @example
 * {
 *   error_key: "errors.export.insufficient_chunks",
 *   error_message: "Insufficient chunks for batch creation",
 *   details: {
 *     available_chunks: 45,
 *     required_chunks: 50,
 *     user_role: "sworik_developer"
 *   },
 *   suggestions: [
 *     {
 *       key: "errors.export.insufficient_chunks.suggestion.wait",
 *       message: "Wait for more chunks to be processed"
 *     }
 *   ]
 * }
 */
export interface StructuredError {
  error_key: string;
  error_message: string;
  details?: Record<string, any>;
  suggestions?: ErrorSuggestion[];
}

/**
 * Represents a translated error ready for display to the user
 *
 * This interface defines the format of errors after they have been processed
 * through the translation system. All text fields are in the user's selected
 * language and ready for display in the UI.
 *
 * @interface TranslatedError
 * @property {string} title - Translated error title/message in the user's selected language
 * @property {string} [message] - Optional additional translated message providing more context
 * @property {Record<string, any>} [details] - Optional contextual information preserved from the structured error
 * @property {string[]} [suggestions] - Optional array of translated suggestion strings ready for display
 *
 * @example
 * {
 *   title: "Insufficient chunks for batch creation",
 *   message: "Not enough audio chunks are available to create an export batch.",
 *   details: {
 *     available_chunks: 45,
 *     required_chunks: 50
 *   },
 *   suggestions: [
 *     "Wait for more chunks to be processed (check back in a few hours)",
 *     "Contact an admin who can create batches with fewer chunks"
 *   ]
 * }
 */
export interface TranslatedError {
  title: string;
  message?: string;
  details?: Record<string, any>;
  suggestions?: string[];
}

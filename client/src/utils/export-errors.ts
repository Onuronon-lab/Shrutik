/**
 * Utility functions for handling export-related errors with enhanced error responses
 */

import type { StructuredErrorResponse, ErrorDetails } from '../features/export/batch/types';
import type { ExportStructuredErrorResponse, ExportErrorDetails } from '../types/export';

// Type guard for structured export errors
export function isExportStructuredError(error: any): error is ExportStructuredErrorResponse {
  return error && typeof error === 'object' && 'error' in error && 'details' in error;
}

// Type guard for batch structured errors
export function isBatchStructuredError(error: any): error is StructuredErrorResponse {
  return error && typeof error === 'object' && 'error' in error && 'details' in error;
}

// Generic structured error check
export function isAnyStructuredError(
  error: any
): error is StructuredErrorResponse | ExportStructuredErrorResponse {
  return isExportStructuredError(error) || isBatchStructuredError(error);
}

// Extract error message from any error format
export function extractErrorMessage(error: any): string {
  if (isAnyStructuredError(error)) {
    return error.error;
  }
  if (error?.response?.data?.error) {
    return error.response.data.error;
  }
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }
  if (error?.message) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unexpected error occurred';
}

// Extract suggestions from structured errors
export function extractErrorSuggestions(error: any): string[] {
  if (isAnyStructuredError(error)) {
    return error.details.suggestions || [];
  }
  if (error?.response?.data?.details?.suggestions) {
    return error.response.data.details.suggestions;
  }
  return [];
}

// Extract error context for display
export function extractErrorContext(error: any): Partial<ErrorDetails | ExportErrorDetails> {
  if (isAnyStructuredError(error)) {
    return error.details;
  }
  if (error?.response?.data?.details) {
    return error.response.data.details;
  }
  return {};
}

// Check if error has actionable suggestions
export function hasActionableSuggestions(error: any): boolean {
  const suggestions = extractErrorSuggestions(error);
  return suggestions.length > 0;
}

// Format quota error information
export function formatQuotaError(context: Partial<ErrorDetails | ExportErrorDetails>): string {
  if (context.downloads_today !== undefined && context.daily_limit !== undefined) {
    const remaining = Math.max(0, context.daily_limit - context.downloads_today);
    if (remaining === 0) {
      const resetInfo = context.hours_until_reset
        ? ` (resets in ${context.hours_until_reset} hours)`
        : '';
      return `Daily download limit reached (${context.downloads_today}/${context.daily_limit})${resetInfo}`;
    }
    return `${remaining} downloads remaining today (${context.downloads_today}/${context.daily_limit})`;
  }
  return '';
}

// Format chunk availability error
export function formatChunkError(context: Partial<ErrorDetails | ExportErrorDetails>): string {
  if (context.available_chunks !== undefined && context.required_chunks !== undefined) {
    return `Only ${context.available_chunks} chunks available, but ${context.required_chunks} required for your role (${context.user_role})`;
  }
  return '';
}

// Get user-friendly error title based on error type
export function getErrorTitle(error: any): string {
  const message = extractErrorMessage(error);

  if (message.toLowerCase().includes('insufficient chunks')) {
    return 'Not Enough Chunks Available';
  }
  if (message.toLowerCase().includes('download limit')) {
    return 'Download Limit Reached';
  }
  if (message.toLowerCase().includes('permission')) {
    return 'Permission Denied';
  }
  if (message.toLowerCase().includes('quota')) {
    return 'Quota Exceeded';
  }

  return 'Export Error';
}

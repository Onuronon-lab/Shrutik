import { useState, useCallback } from 'react';

interface StructuredError {
  error: string;
  details?: {
    [key: string]: any;
  };
}

interface UseErrorHandlerReturn {
  error: string | StructuredError | null;
  setError: (error: string | StructuredError | null) => void;
  clearError: () => void;
  handleError: (error: any) => void;
}

export function useErrorHandler(): UseErrorHandlerReturn {
  const [error, setErrorState] = useState<string | StructuredError | null>(null);

  const setError = useCallback((error: string | StructuredError | null) => {
    setErrorState(error);
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  const handleError = useCallback((error: any) => {
    // Check if the error response has a structured format
    if (error?.response?.data?.error && typeof error.response.data.error === 'string') {
      // Structured error with details
      const structuredError: StructuredError = {
        error: error.response.data.error,
        details: error.response.data.details || {},
      };
      setErrorState(structuredError);
    } else if (error?.response?.data?.error?.message) {
      setErrorState(error.response.data.error.message);
    } else if (error?.response?.data?.detail) {
      // Check if detail is a structured error
      if (typeof error.response.data.detail === 'object' && error.response.data.detail.error) {
        setErrorState(error.response.data.detail);
      } else {
        setErrorState(error.response.data.detail);
      }
    } else if (error?.message) {
      setErrorState(error.message);
    } else if (error?.request) {
      setErrorState('No response from server. It might be offline.');
    } else {
      setErrorState('An unexpected error occurred');
    }
  }, []);

  return { error, setError, clearError, handleError };
}

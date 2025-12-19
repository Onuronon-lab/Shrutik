import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

interface UseErrorHandlerReturn {
  error: string | null;
  setError: (error: string | null) => void;
  clearError: () => void;
  handleError: (error: any) => void;
}

export function useErrorHandler(): UseErrorHandlerReturn {
  const [error, setErrorState] = useState<string | null>(null);
  const { t } = useTranslation();

  const setError = useCallback((error: string | null) => {
    setErrorState(error);
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  const handleError = useCallback((error: any) => {
    if (error?.response?.data?.error?.message) {
      setErrorState(error.response.data.error.message);
    } else if (error?.response?.data?.detail) {
      setErrorState(error.response.data.detail);
    } else if (error?.message) {
      setErrorState(error.message);
    } else if (error?.request) {
      setErrorState(t('server-offline-error'));
    } else {
      setErrorState(t('unexpected-error'));
    }
  }, []);

  return { error, setError, clearError, handleError };
}

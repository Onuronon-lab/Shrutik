import { DependencyList, useCallback, useEffect, useState } from 'react';

interface UseAsyncResourceOptions {
  /**
   * Whether the hook should invoke the loader immediately.
   * Defaults to true.
   */
  immediate?: boolean;
  /**
   * Optional mapper to extract a user-friendly error message.
   */
  errorMapper?: (error: unknown) => string;
}

interface UseAsyncResourceResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<T>;
  setData: (value: T | null) => void;
  setError: (value: string | null) => void;
}

const defaultErrorMapper = (error: unknown) => {
  if (typeof error === 'string') {
    return error;
  }
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    (error as any).response?.data?.detail
  ) {
    return (error as any).response.data.detail;
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return (error as any).message;
  }
  return 'Something went wrong. Please try again.';
};

export function useAsyncResource<T>(
  loader: () => Promise<T>,
  deps: DependencyList = [],
  options: UseAsyncResourceOptions = {}
): UseAsyncResourceResult<T> {
  const { immediate = true, errorMapper = defaultErrorMapper } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await loader();
      setData(result);
      return result;
    } catch (err) {
      const message = errorMapper(err);
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loader, errorMapper, ...deps]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execute, immediate]);

  return { data, loading, error, refresh: execute, setData, setError };
}

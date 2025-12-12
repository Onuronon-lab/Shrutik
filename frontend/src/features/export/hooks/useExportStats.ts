import { useEffect } from 'react';
import { exportService } from '../../../services/export.service';
import { useAsyncResource } from '../../../hooks/useAsyncResource';

export function useExportStats(shouldLoad: boolean) {
  const { data, loading, error, refresh } = useAsyncResource(
    () => exportService.getExportStatistics(),
    [],
    { immediate: false }
  );

  useEffect(() => {
    if (shouldLoad) {
      refresh();
    }
  }, [shouldLoad, refresh]);

  return { stats: data, loading, error };
}

import { useCallback, useEffect, useState } from 'react';
import { exportService } from '../../../../services/export.service';
import type { DownloadQuota } from '../types';

interface UseDownloadQuotaOptions {
  enabled: boolean;
}

export function useDownloadQuota({ enabled }: UseDownloadQuotaOptions) {
  const [quota, setQuota] = useState<DownloadQuota | null>(null);
  const [loading, setLoading] = useState(false);

  const loadQuota = useCallback(async () => {
    if (!enabled) return;

    try {
      setLoading(true);
      const quotaData = await exportService.getDownloadQuota();
      setQuota(quotaData);
    } catch (error) {
      console.error('Failed to load quota:', error);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    loadQuota();
  }, [loadQuota]);

  return {
    quota,
    loading,
    refresh: loadQuota,
    setQuota,
  };
}

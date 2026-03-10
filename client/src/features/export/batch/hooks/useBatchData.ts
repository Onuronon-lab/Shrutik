import { useCallback, useEffect, useState } from 'react';
import { exportService } from '../../../../services/export.service';
import type { ExportBatch } from '../types';

interface UseBatchDataOptions {
  enabled: boolean;
  onError?: (message: string | null) => void;
  defaultErrorMessage: string;
}

export function useBatchData({ enabled, onError, defaultErrorMessage }: UseBatchDataOptions) {
  const [batches, setBatches] = useState<ExportBatch[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const loadBatches = useCallback(async () => {
    if (!enabled) return;

    try {
      setLoading(true);
      onError?.(null);

      const params: Record<string, string | number> = {
        page,
        page_size: 10,
      };

      if (statusFilter) {
        params.status_filter = statusFilter;
      }

      const response = await exportService.listExportBatches(params);
      setBatches(response.batches || []);
      setTotalCount(response.total_count || 0);
    } catch (err: any) {
      // Handle batch loading errors
      if (err.response?.status === 401 || err.response?.status === 404) {
        setBatches([]);
        setTotalCount(0);
        onError?.(null);
        return;
      }

      if (err.response?.status === 500) {
        onError?.('Server error. Please ensure database migrations are run: alembic upgrade head');
        setBatches([]);
        setTotalCount(0);
        return;
      }

      const message = err.response?.data?.detail || defaultErrorMessage;
      onError?.(message);
      setBatches([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [enabled, page, statusFilter, defaultErrorMessage]); // Removed onError from dependencies

  useEffect(() => {
    loadBatches();
  }, [loadBatches]);

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  return {
    batches,
    totalCount,
    page,
    setPage,
    statusFilter,
    setStatusFilter: handleStatusFilterChange,
    loading,
    refresh: loadBatches,
  };
}

import { useCallback, useEffect, useState } from 'react';
import { exportService } from '../../../services/export.service';
import { ExportHistoryResponse } from '../../../types/export';
import { ExportHistoryFilters } from '../types';

interface UseExportHistoryOptions {
  isActive: boolean;
  refreshToken: number;
}

const initialFilters: ExportHistoryFilters = {
  export_type: '',
  date_from: '',
  date_to: '',
};

export function useExportHistory({ isActive, refreshToken }: UseExportHistoryOptions) {
  const [filters, setFiltersState] = useState<ExportHistoryFilters>(initialFilters);
  const [page, setPage] = useState(1);
  const [history, setHistory] = useState<ExportHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    if (!isActive) return;

    setLoading(true);
    setError(null);

    try {
      const params = {
        page,
        page_size: 20,
        ...(filters.export_type && { export_type: filters.export_type }),
        ...(filters.date_from && { date_from: filters.date_from }),
        ...(filters.date_to && { date_to: filters.date_to }),
      };
      const response = await exportService.getExportHistory(params);
      setHistory(response);
    } catch (err) {
      console.error('Failed to load export history:', err);
      setError('Failed to load export history');
    } finally {
      setLoading(false);
    }
  }, [filters, isActive, page]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory, refreshToken]);

  const setFilters = (
    updater: ExportHistoryFilters | ((prev: ExportHistoryFilters) => ExportHistoryFilters)
  ) => {
    setPage(1);
    setFiltersState(prev => (typeof updater === 'function' ? (updater as any)(prev) : updater));
  };

  return {
    history,
    loading,
    error,
    filters,
    setFilters,
    page,
    setPage,
    refresh: loadHistory,
  };
}

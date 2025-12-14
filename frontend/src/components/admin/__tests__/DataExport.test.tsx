import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

const mockUseAuth = vi.fn();
const mockUseExportStats = vi.fn();
const mockUseExportHistory = vi.fn();
const mockExportDataset = vi.fn();
const mockExportMetadata = vi.fn();
const mockT = vi.fn();

vi.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('../../../services/export.service', () => ({
  exportService: {
    exportDataset: (...args: unknown[]) => mockExportDataset(...args),
    exportMetadata: (...args: unknown[]) => mockExportMetadata(...args),
  },
}));

vi.mock('../../../features/export/hooks/useExportStats', () => ({
  useExportStats: (...args: unknown[]) => mockUseExportStats(...args),
}));

vi.mock('../../../features/export/hooks/useExportHistory', () => ({
  useExportHistory: (...args: unknown[]) => mockUseExportHistory(...args),
}));

vi.mock('../../../features/export/components/DatasetExportForm', () => ({
  DatasetExportForm: ({ t }: { t: (key: string) => string }) => (
    <div data-testid="dataset-form">{t('dataExport-exportButton')}</div>
  ),
}));

vi.mock('../../../features/export/components/MetadataExportPanel', () => ({
  MetadataExportPanel: () => <div data-testid="metadata-panel" />,
}));

vi.mock('../../../features/export/components/PlatformStatsOverview', () => ({
  PlatformStatsOverview: () => <div data-testid="stats-overview" />,
}));

vi.mock('../../../features/export/components/ExportHistoryPanel', () => ({
  ExportHistoryPanel: () => <div data-testid="history-panel" />,
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, vars?: Record<string, unknown>) => mockT(key, vars),
    i18n: { language: 'en' },
  }),
}));

import DataExport from '../DataExport';

const renderComponent = (component: React.ReactElement) => render(component);

beforeEach(() => {
  mockUseAuth.mockReturnValue({
    user: {
      id: 1,
      name: 'Test Developer',
      email: 'developer@sworik.com',
      role: 'sworik_developer',
    },
    token: 'mock-token',
    login: vi.fn(),
    logout: vi.fn(),
    isAuthenticated: true,
    isLoading: false,
  });

  mockUseExportStats.mockReturnValue({
    stats: {
      total_recordings: 100,
      total_chunks: 500,
      total_transcriptions: 1000,
      validated_transcriptions: 800,
    },
    loading: false,
    error: null,
  });

  mockUseExportHistory.mockReturnValue({
    history: {
      logs: [],
      total_count: 0,
      page_size: 20,
    },
    loading: false,
    error: null,
    filters: {},
    setFilters: vi.fn(),
    page: 1,
    setPage: vi.fn(),
  });

  mockExportDataset.mockResolvedValue({
    export_id: 'export-123',
    total_records: 120,
    data: { sample: true },
  });

  mockExportMetadata.mockResolvedValue({
    export_id: 'meta-123',
    statistics: {},
    platform_metrics: {},
  });

  mockT.mockImplementation((key: string, vars?: Record<string, unknown>) => {
    if (vars && typeof vars.count !== 'undefined') {
      return `${key}-${vars.count}`;
    }
    return key;
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('DataExport Component', () => {
  it('renders data export interface for Sworik developer', () => {
    renderComponent(<DataExport />);

    expect(screen.getByText('dataExport-title')).toBeInTheDocument();
    expect(screen.getByText('dataExport-subtitle')).toBeInTheDocument();

    expect(screen.getByText('exportTab-dataset')).toBeInTheDocument();
    expect(screen.getByText('exportTab-metadata')).toBeInTheDocument();
    expect(screen.getByText('exportTab-history')).toBeInTheDocument();

    expect(screen.getByTestId('stats-overview')).toBeInTheDocument();
  });

  it('shows dataset export form by default', () => {
    renderComponent(<DataExport />);

    expect(screen.getByTestId('dataset-form')).toHaveTextContent('dataExport-exportButton');
  });
});

describe('DataExport Access Control', () => {
  it('shows access denied message for unauthorized role', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 2,
        name: 'Test Contributor',
        email: 'contributor@example.com',
        role: 'contributor',
      },
      token: 'mock-token',
      login: vi.fn(),
      logout: vi.fn(),
      isAuthenticated: true,
      isLoading: false,
    });

    renderComponent(<DataExport />);

    expect(screen.getByText('access_denied')).toBeInTheDocument();
    expect(screen.getByText('export_restricted')).toBeInTheDocument();
    expect(screen.queryByTestId('dataset-form')).not.toBeInTheDocument();
  });
});

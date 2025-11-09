import React from 'react';
import { render, screen } from '@testing-library/react';
import DataExport from '../DataExport';

// Mock the API service
jest.mock('../../../services/api', () => ({
  apiService: {
    getExportStatistics: jest.fn().mockResolvedValue({
      statistics: {
        total_recordings: 100,
        total_chunks: 500,
        total_transcriptions: 1000,
        validated_transcriptions: 800
      }
    }),
    getExportHistory: jest.fn().mockResolvedValue({
      logs: [],
      total_count: 0,
      page: 1,
      page_size: 20
    }),
    exportDataset: jest.fn(),
    exportMetadata: jest.fn()
  }
}));

// Mock the useAuth hook
jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      name: 'Test Developer',
      email: 'developer@sworik.com',
      role: 'sworik_developer'
    },
    token: 'mock-token',
    login: jest.fn(),
    logout: jest.fn(),
    isAuthenticated: true,
    isLoading: false
  })
}));

const renderComponent = (component: React.ReactElement) => {
  return render(component);
};

describe('DataExport Component', () => {
  test('renders data export interface for sworik developer', () => {
    renderComponent(<DataExport />);
    
    // Check if main heading is present
    expect(screen.getByText('Data Export')).toBeInTheDocument();
    expect(screen.getByText('Export validated datasets and platform metadata for AI training')).toBeInTheDocument();
    
    // Check if tabs are present
    expect(screen.getByText('Dataset Export')).toBeInTheDocument();
    expect(screen.getByText('Metadata Export')).toBeInTheDocument();
    expect(screen.getByText('Export History')).toBeInTheDocument();
  });

  test('shows dataset export form by default', () => {
    renderComponent(<DataExport />);
    
    // Check if dataset export form elements are present
    expect(screen.getByText('Export Format')).toBeInTheDocument();
    expect(screen.getByText('Quality Filters')).toBeInTheDocument();
    // Use getAllByText to handle multiple instances
    expect(screen.getAllByText('Export Dataset')[0]).toBeInTheDocument();
  });
});

describe('DataExport Access Control', () => {
  test('shows access denied for non-sworik developer', () => {
    // Mock useAuth to return a contributor user
    jest.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        user: {
          id: 1,
          name: 'Test Contributor',
          email: 'contributor@example.com',
          role: 'contributor'
        },
        token: 'mock-token',
        login: jest.fn(),
        logout: jest.fn(),
        isAuthenticated: true,
        isLoading: false
      })
    }));

    // Re-import the component to get the new mock
    const DataExportWithContributor = require('../DataExport').default;
    
    renderComponent(<DataExportWithContributor />);
    
    // Check if access denied message is shown
    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText('Data export functionality is restricted to Admins and Sworik developers only.')).toBeInTheDocument();
  });
});
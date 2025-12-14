import React from 'react';
import { render, screen, act } from '@testing-library/react';

vi.mock('react-router-dom', () => {
  const React = require('react');
  return {
    BrowserRouter: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="router">{children}</div>
    ),
    Routes: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="routes">{children}</div>
    ),
    Route: ({ element, children }: { element: React.ReactNode; children?: React.ReactNode }) => (
      <>
        <div data-testid="route">{element}</div>
        {children}
      </>
    ),
  };
});

vi.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
}));

vi.mock('./components/auth/ProtectedRoute', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  ),
}));

vi.mock('./components/layout/Layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

vi.mock('./components/auth/LoginForm', () => ({
  default: () => <div>login-form</div>,
}));

vi.mock('./components/auth/RegisterForm', () => ({
  default: () => <div>register-form</div>,
}));

vi.mock('./components/common/LoadingSpinner', () => ({
  default: () => <div>loading-spinner</div>,
}));

vi.mock('./pages/HomePage', () => ({ default: () => <div>home-page</div> }));
vi.mock('./pages/RecordPage', () => ({
  default: () => <div>record-page</div>,
}));
vi.mock('./pages/TranscribePage', () => ({
  default: () => <div>transcribe-page</div>,
}));
vi.mock('./pages/AdminPage', () => ({ default: () => <div>admin-page</div> }));
vi.mock('./pages/ExportPage', () => ({
  default: () => <div>export-page</div>,
}));
vi.mock('./pages/UnauthorizedPage', () => ({
  default: () => <div>unauthorized-page</div>,
}));

import App from './App';

test('App mounts with routing shell', async () => {
  await act(async () => {
    render(<App />);
  });

  expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
  expect(screen.getByTestId('router')).toBeInTheDocument();
  expect(screen.getAllByTestId('route')).not.toHaveLength(0);
});

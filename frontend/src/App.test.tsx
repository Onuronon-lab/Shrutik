import React from 'react';
import { render, screen, act } from '@testing-library/react';

jest.mock(
  'react-router-dom',
  () => {
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
  },
  { virtual: true }
);

jest.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
}));

jest.mock('./components/auth/ProtectedRoute', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  ),
}));

jest.mock('./components/layout/Layout', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

jest.mock('./components/auth/LoginForm', () => ({
  __esModule: true,
  default: () => <div>login-form</div>,
}));

jest.mock('./components/auth/RegisterForm', () => ({
  __esModule: true,
  default: () => <div>register-form</div>,
}));

jest.mock('./components/common/LoadingSpinner', () => ({
  __esModule: true,
  default: () => <div>loading-spinner</div>,
}));

jest.mock('./pages/HomePage', () => ({ __esModule: true, default: () => <div>home-page</div> }));
jest.mock('./pages/RecordPage', () => ({
  __esModule: true,
  default: () => <div>record-page</div>,
}));
jest.mock('./pages/TranscribePage', () => ({
  __esModule: true,
  default: () => <div>transcribe-page</div>,
}));
jest.mock('./pages/AdminPage', () => ({ __esModule: true, default: () => <div>admin-page</div> }));
jest.mock('./pages/ExportPage', () => ({
  __esModule: true,
  default: () => <div>export-page</div>,
}));
jest.mock('./pages/UnauthorizedPage', () => ({
  __esModule: true,
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

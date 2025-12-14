import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/layout/Layout';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import LoadingSpinner from './components/common/LoadingSpinner';

// Lazy load pages for better performance
const HomePage = lazy(() => import('./pages/HomePage'));
const RecordPage = lazy(() => import('./pages/RecordPage'));
const TranscribePage = lazy(() => import('./pages/TranscribePage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const ExportPage = lazy(() => import('./pages/ExportPage'));
const UnauthorizedPage = lazy(() => import('./pages/UnauthorizedPage'));

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route
            path="/unauthorized"
            element={
              <Suspense fallback={<LoadingSpinner />}>
                <UnauthorizedPage />
              </Suspense>
            }
          />
          <Route path="/" element={<Layout />}>
            <Route
              index
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingSpinner />}>
                    <HomePage />
                  </Suspense>
                </ProtectedRoute>
              }
            />
            <Route
              path="/record"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingSpinner />}>
                    <RecordPage />
                  </Suspense>
                </ProtectedRoute>
              }
            />
            <Route
              path="/transcribe"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingSpinner />}>
                    <TranscribePage />
                  </Suspense>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <Suspense fallback={<LoadingSpinner />}>
                    <AdminPage />
                  </Suspense>
                </ProtectedRoute>
              }
            />
            <Route
              path="/export"
              element={
                <ProtectedRoute requiredRole={['admin', 'sworik_developer']}>
                  <Suspense fallback={<LoadingSpinner />}>
                    <ExportPage />
                  </Suspense>
                </ProtectedRoute>
              }
            />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

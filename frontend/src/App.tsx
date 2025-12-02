import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/layout/Layout';
import LoginForm from './components/auth/LoginForm';
import HomePage from './pages/HomePage';
import RecordPage from './pages/RecordPage';
import TranscribePage from './pages/TranscribePage';
import AdminPage from './pages/AdminPage';
import ExportPage from './pages/ExportPage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import RegisterForm from './components/auth/RegisterForm';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route path="/" element={<Layout />}>
            <Route
              index
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/record"
              element={
                <ProtectedRoute>
                  <RecordPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/transcribe"
              element={
                <ProtectedRoute>
                  <TranscribePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/export"
              element={
                <ProtectedRoute requiredRole={['admin', 'sworik_developer']}>
                  <ExportPage />
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

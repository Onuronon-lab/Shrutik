import React, { Suspense, ReactNode } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface LoadingBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
}

/**
 * Loading boundary component for wrapping lazy-loaded components
 * Provides consistent loading states across the application
 */
const LoadingBoundary: React.FC<LoadingBoundaryProps> = ({
  children,
  fallback,
  className = '',
}) => {
  const defaultFallback = (
    <div className={`flex items-center justify-center py-8 ${className}`}>
      <LoadingSpinner />
    </div>
  );

  return <Suspense fallback={fallback || defaultFallback}>{children}</Suspense>;
};

export default LoadingBoundary;

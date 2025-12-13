import React, { Suspense, ComponentType } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface LazyWrapperProps {
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * Wrapper component for lazy-loaded components with loading boundary
 */
const LazyWrapper: React.FC<LazyWrapperProps> = ({ fallback = <LoadingSpinner />, children }) => {
  return <Suspense fallback={fallback}>{children}</Suspense>;
};

/**
 * Higher-order component for creating lazy-loaded components with loading boundaries
 */
export function withLazyLoading<P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) {
  const LazyComponent = React.lazy(() => Promise.resolve({ default: Component }));

  return React.forwardRef<any, P>((props, ref) => (
    <LazyWrapper fallback={fallback}>
      <LazyComponent {...props} ref={ref} />
    </LazyWrapper>
  ));
}

/**
 * Create a lazy-loaded component from a dynamic import
 */
export function createLazyComponent<P extends object>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  fallback?: React.ReactNode
) {
  const LazyComponent = React.lazy(importFn);

  return React.forwardRef<any, P>((props, ref) => (
    <LazyWrapper fallback={fallback}>
      <LazyComponent {...props} ref={ref} />
    </LazyWrapper>
  ));
}

export default LazyWrapper;

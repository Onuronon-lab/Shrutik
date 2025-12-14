import React from 'react';
import { DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { Script } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';
import { DurationOption } from './DurationSelector';

interface ScriptViewerProps {
  selectedDuration: DurationOption;
  currentScript: Script | null;
  isLoading: boolean;
  error: string | null;
  onChangeDuration: () => void;
  onRetryLoad: () => void;
  className?: string;
  'data-testid'?: string;
}

const ScriptViewer: React.FC<ScriptViewerProps> = ({
  selectedDuration,
  currentScript,
  isLoading,
  error,
  onChangeDuration,
  onRetryLoad,
  className = '',
  'data-testid': testId,
}) => {
  return (
    <div
      className={`bg-card rounded-lg shadow-md p-6 border border-border ${className}`}
      data-testid={testId}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-foreground flex items-center">
          <DocumentTextIcon className="w-5 h-5 mr-2" />
          Script ({selectedDuration.label})
        </h2>
        <button
          onClick={onChangeDuration}
          className="text-sm text-primary hover:text-primary-hover"
          data-testid="change-duration-button"
        >
          Change Duration
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8" data-testid="loading-state">
          <LoadingSpinner size="md" />
          <span className="ml-2 text-secondary-foreground">Loading script...</span>
        </div>
      ) : currentScript ? (
        <div className="bg-nutral rounded-lg p-4 mb-4" data-testid="script-content">
          <div className="text-lg leading-relaxed text-foreground font-bengali">
            {currentScript.text}
          </div>
        </div>
      ) : error ? (
        <div
          className="bg-destructive border border-destructive-border rounded-lg p-4 mb-4"
          data-testid="error-state"
        >
          <div className="flex items-center text-destructive-foreground">
            <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
            {error}
          </div>
          <button
            onClick={onRetryLoad}
            className="mt-2 text-sm text-destructive-foreground hover:text-destructive-foreground hover:underline"
            data-testid="retry-button"
          >
            Try Again
          </button>
        </div>
      ) : null}
    </div>
  );
};

export default ScriptViewer;

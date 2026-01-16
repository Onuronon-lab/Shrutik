import React from 'react';
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';
import { TranslatedError } from '../../../../types/errors';

interface BatchFeedbackProps {
  error?: TranslatedError | null;
  success?: string | null;
}

export const BatchFeedback: React.FC<BatchFeedbackProps> = ({ error, success }) => {
  if (!error && !success) return null;

  if (success) {
    return (
      <div
        className="border rounded-lg p-4 mb-6 bg-success border-success-border text-success-foreground"
        role="alert"
        aria-live="polite"
      >
        <div className="flex items-center">
          <CheckCircleIcon className="h-5 w-5 mr-2" aria-hidden="true" />
          <p>{success}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="border rounded-lg p-4 mb-6 bg-destructive border-destructive-border text-destructive-foreground"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
      >
        <div className="flex items-start">
          <ExclamationTriangleIcon
            className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0"
            aria-hidden="true"
          />
          <div className="flex-1">
            {/* Error Title */}
            <p className="font-medium" aria-label="Error message">
              {error.title}
            </p>

            {/* Optional Error Message */}
            {error.message && <p className="mt-2 text-sm">{error.message}</p>}

            {/* Error Details */}
            {error.details && Object.keys(error.details).length > 0 && (
              <div className="mt-3 space-y-2">
                {/* Insufficient chunks context */}
                {error.details.available_chunks !== undefined &&
                  error.details.required_chunks !== undefined && (
                    <div
                      className="bg-destructive/10 border border-destructive/20 rounded p-3"
                      role="region"
                      aria-label="Error context"
                    >
                      <div className="flex items-center mb-2">
                        <InformationCircleIcon className="h-4 w-4 mr-1" aria-hidden="true" />
                        <span className="text-sm font-medium">Context:</span>
                      </div>
                      <div className="text-sm space-y-1">
                        <div>
                          Available chunks:{' '}
                          <span className="font-medium">{error.details.available_chunks}</span>
                        </div>
                        <div>
                          Required chunks:{' '}
                          <span className="font-medium">{error.details.required_chunks}</span>
                        </div>
                        {error.details.user_role && (
                          <div>
                            Your role:{' '}
                            <span className="font-medium">{error.details.user_role}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                {/* Quota exhaustion context */}
                {error.details.downloads_today !== undefined &&
                  error.details.daily_limit !== undefined && (
                    <div
                      className="bg-destructive/10 border border-destructive/20 rounded p-3"
                      role="region"
                      aria-label="Quota status"
                    >
                      <div className="flex items-center mb-2">
                        <InformationCircleIcon className="h-4 w-4 mr-1" aria-hidden="true" />
                        <span className="text-sm font-medium">Quota Status:</span>
                      </div>
                      <div className="text-sm space-y-1">
                        <div>
                          Downloads today:{' '}
                          <span className="font-medium">
                            {error.details.downloads_today}/{error.details.daily_limit}
                          </span>
                        </div>
                        {error.details.reset_time && (
                          <div>
                            Resets at:{' '}
                            <span className="font-medium">
                              {new Date(error.details.reset_time).toLocaleString()}
                            </span>
                          </div>
                        )}
                        {error.details.hours_until_reset !== undefined && (
                          <div>
                            Time remaining:{' '}
                            <span className="font-medium">
                              {error.details.hours_until_reset} hours
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
              </div>
            )}

            {/* Suggestions */}
            {error.suggestions && error.suggestions.length > 0 && (
              <div
                className="mt-3 bg-info/10 border border-info/20 rounded p-3"
                role="region"
                aria-label="Suggestions to resolve error"
              >
                <div className="flex items-center mb-2">
                  <LightBulbIcon className="h-4 w-4 mr-1 text-info" aria-hidden="true" />
                  <span className="text-sm font-medium text-info">Suggestions:</span>
                </div>
                <ul className="text-sm text-info-foreground space-y-1.5" role="list">
                  {error.suggestions.map((suggestion: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2 mt-0.5" aria-hidden="true">
                        •
                      </span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

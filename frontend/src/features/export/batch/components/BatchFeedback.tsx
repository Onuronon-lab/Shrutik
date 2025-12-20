import React from 'react';
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

interface StructuredError {
  error: string;
  details?: {
    available_chunks?: number;
    required_chunks?: number;
    user_role?: string;
    downloads_today?: number;
    daily_limit?: number;
    reset_time?: string;
    hours_until_reset?: number;
    suggestions?: string[];
    [key: string]: any;
  };
}

interface BatchFeedbackProps {
  error?: string | StructuredError | null;
  success?: string | null;
}

const isStructuredError = (error: any): error is StructuredError => {
  return error && typeof error === 'object' && 'error' in error;
};

export const BatchFeedback: React.FC<BatchFeedbackProps> = ({ error, success }) => {
  if (!error && !success) return null;

  if (success) {
    return (
      <div className="border rounded-lg p-4 mb-6 bg-success border-success-border text-success-foreground">
        <div className="flex items-center">
          <CheckCircleIcon className="h-5 w-5 mr-2" />
          <p>{success}</p>
        </div>
      </div>
    );
  }

  if (error) {
    const isStructured = isStructuredError(error);
    const errorMessage = isStructured ? error.error : String(error);
    const details = isStructured ? error.details : null;

    return (
      <div className="border rounded-lg p-4 mb-6 bg-destructive border-destructive-border text-destructive-foreground">
        <div className="flex items-start">
          <ExclamationTriangleIcon className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-medium">{errorMessage}</p>

            {/* Display error context */}
            {details && (
              <div className="mt-3 space-y-2">
                {/* Insufficient chunks context */}
                {details.available_chunks !== undefined &&
                  details.required_chunks !== undefined && (
                    <div className="bg-destructive/10 border border-destructive/20 rounded p-3">
                      <div className="flex items-center mb-2">
                        <InformationCircleIcon className="h-4 w-4 mr-1" />
                        <span className="text-sm font-medium">Context:</span>
                      </div>
                      <div className="text-sm space-y-1">
                        <div>
                          Available chunks:{' '}
                          <span className="font-medium">{details.available_chunks}</span>
                        </div>
                        <div>
                          Required for {details.user_role}:{' '}
                          <span className="font-medium">{details.required_chunks}</span>
                        </div>
                      </div>
                    </div>
                  )}

                {/* Quota exhaustion context */}
                {details.downloads_today !== undefined && details.daily_limit !== undefined && (
                  <div className="bg-destructive/10 border border-destructive/20 rounded p-3">
                    <div className="flex items-center mb-2">
                      <InformationCircleIcon className="h-4 w-4 mr-1" />
                      <span className="text-sm font-medium">Quota Status:</span>
                    </div>
                    <div className="text-sm space-y-1">
                      <div>
                        Downloads today:{' '}
                        <span className="font-medium">
                          {details.downloads_today}/{details.daily_limit}
                        </span>
                      </div>
                      {details.reset_time && (
                        <div>
                          Resets at:{' '}
                          <span className="font-medium">
                            {new Date(details.reset_time).toLocaleString()}
                          </span>
                        </div>
                      )}
                      {details.hours_until_reset && (
                        <div>
                          Time remaining:{' '}
                          <span className="font-medium">{details.hours_until_reset} hours</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Suggestions */}
                {details.suggestions && details.suggestions.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded p-3">
                    <div className="flex items-center mb-2">
                      <LightBulbIcon className="h-4 w-4 mr-1 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">Suggestions:</span>
                    </div>
                    <ul className="text-sm text-blue-800 space-y-1">
                      {details.suggestions.map((suggestion, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">•</span>
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

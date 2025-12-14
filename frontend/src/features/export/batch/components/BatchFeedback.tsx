import React from 'react';
import { ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface BatchFeedbackProps {
  error?: string | null;
  success?: string | null;
}

export const BatchFeedback: React.FC<BatchFeedbackProps> = ({ error, success }) => {
  if (!error && !success) return null;

  const isError = Boolean(error);
  const Icon = isError ? ExclamationTriangleIcon : CheckCircleIcon;
  const message = error || success || '';

  return (
    <div
      className={`border rounded-lg p-4 mb-6 ${
        isError
          ? 'bg-destructive border-destructive-border text-destructive-foreground'
          : 'bg-success border-success-border text-success-foreground'
      }`}
    >
      <div className="flex items-center">
        <Icon className="h-5 w-5 mr-2" />
        <p>{message}</p>
      </div>
    </div>
  );
};

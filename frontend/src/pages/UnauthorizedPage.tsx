import React from 'react';
import { Link } from 'react-router-dom';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const UnauthorizedPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full text-center">
        <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-destructive mb-4" />
        <h1 className="text-2xl font-bold text-foreground mb-2">Access Denied</h1>
        <p className="text-secondary-foreground mb-6">
          You don't have permission to access this page.
        </p>
        <Link
          to="/"
          className="bg-primary hover:bg-primary-hover text-primary-foreground px-6 py-2 rounded-md text-sm font-medium transition-colors"
        >
          Go Home
        </Link>
      </div>
    </div>
  );
};

export default UnauthorizedPage;
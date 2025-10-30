import React from 'react';
import { Cog6ToothIcon } from '@heroicons/react/24/outline';

const AdminPage: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <Cog6ToothIcon className="mx-auto h-16 w-16 text-purple-600 mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">
          Manage users, scripts, and monitor platform activity
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-8 border border-gray-200">
        <div className="text-center text-gray-500">
          <p className="text-lg mb-4">Admin dashboard will be implemented in a later task.</p>
          <p>This will include:</p>
          <ul className="text-left max-w-md mx-auto mt-4 space-y-2">
            <li>• User management</li>
            <li>• Script repository management</li>
            <li>• Quality review interface</li>
            <li>• Platform statistics</li>
            <li>• Data export controls</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
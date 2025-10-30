import React from 'react';
import { MicrophoneIcon } from '@heroicons/react/24/outline';

const RecordPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <MicrophoneIcon className="mx-auto h-16 w-16 text-indigo-600 mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Voice Recording</h1>
        <p className="text-gray-600">
          Record your voice reading Bangla scripts to help train AI models
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-8 border border-gray-200">
        <div className="text-center text-gray-500">
          <p className="text-lg mb-4">Voice recording interface will be implemented in the next task.</p>
          <p>This will include:</p>
          <ul className="text-left max-w-md mx-auto mt-4 space-y-2">
            <li>• Duration selection (2, 5, 10 minutes)</li>
            <li>• Random script display</li>
            <li>• Real-time audio recording</li>
            <li>• Progress tracking</li>
            <li>• Upload functionality</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RecordPage;
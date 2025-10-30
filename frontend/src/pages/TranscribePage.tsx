import React from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';

const TranscribePage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <DocumentTextIcon className="mx-auto h-16 w-16 text-green-600 mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Audio Transcription</h1>
        <p className="text-gray-600">
          Listen to audio clips and provide accurate Bangla transcriptions
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-8 border border-gray-200">
        <div className="text-center text-gray-500">
          <p className="text-lg mb-4">Transcription interface will be implemented in the next task.</p>
          <p>This will include:</p>
          <ul className="text-left max-w-md mx-auto mt-4 space-y-2">
            <li>• Sentence quantity selection</li>
            <li>• Audio playback controls</li>
            <li>• Bangla text input</li>
            <li>• Skip functionality</li>
            <li>• Progress tracking</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TranscribePage;
import React from 'react';
import { PlayIcon, PauseIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { FlaggedTranscription } from '../../types/api';
import { Button } from '../ui';

interface FlaggedTranscriptionsListProps {
  transcriptions: FlaggedTranscription[];
  playingAudio: number | null;
  onPlayAudio: (transcriptionId: number) => void;
  onStopAudio: () => void;
  onReview: (transcription: FlaggedTranscription) => void;
}

const FlaggedTranscriptionsList: React.FC<FlaggedTranscriptionsListProps> = ({
  transcriptions,
  playingAudio,
  onPlayAudio,
  onStopAudio,
  onReview,
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (transcriptions.length === 0) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
          No flagged transcriptions
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          All transcriptions are within quality thresholds.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {transcriptions.map(item => (
        <div
          key={item.transcription_id}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                  Quality Score: {Math.round(item.quality_score * 100)}%
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">
                  Confidence: {Math.round(item.confidence_score * 100)}%
                </span>
              </div>

              <p className="text-sm text-gray-900 dark:text-white mb-2">{item.text}</p>

              <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                <p>Contributor: {item.contributor_name}</p>
                <p>Created: {formatDate(item.created_at)}</p>
                <p>Reviews: {item.review_count}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2 ml-4">
              <button
                onClick={() =>
                  playingAudio === item.transcription_id
                    ? onStopAudio()
                    : onPlayAudio(item.transcription_id)
                }
                className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {playingAudio === item.transcription_id ? (
                  <PauseIcon className="h-5 w-5" />
                ) : (
                  <PlayIcon className="h-5 w-5" />
                )}
              </button>

              <Button onClick={() => onReview(item)} variant="primary" size="sm">
                Review
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FlaggedTranscriptionsList;

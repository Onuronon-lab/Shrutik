import React from 'react';
import { StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { FlaggedTranscription } from '../../types/api';
import { Button } from '../ui';

interface QualityReviewFormProps {
  reviewingItem: FlaggedTranscription;
  reviewForm: {
    decision: string;
    rating: number;
    comment: string;
  };
  submitting: boolean;
  onFormChange: (field: string, value: any) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

const QualityReviewForm: React.FC<QualityReviewFormProps> = ({
  reviewingItem,
  reviewForm,
  submitting,
  onFormChange,
  onSubmit,
  onCancel,
}) => {
  const renderStars = () => {
    return Array.from({ length: 5 }, (_, i) => {
      const starNumber = i + 1;
      const isFilled = starNumber <= reviewForm.rating;

      return (
        <button
          key={i}
          type="button"
          onClick={() => onFormChange('rating', starNumber)}
          className="text-yellow-400 hover:text-yellow-500"
        >
          {isFilled ? <StarIconSolid className="h-6 w-6" /> : <StarIcon className="h-6 w-6" />}
        </button>
      );
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Review Transcription
        </h3>
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <p className="text-sm text-gray-900 dark:text-white">{reviewingItem.text}</p>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            <p>Contributor: {reviewingItem.contributor_name}</p>
            <p>Quality Score: {Math.round(reviewingItem.quality_score * 100)}%</p>
            <p>Confidence Score: {Math.round(reviewingItem.confidence_score * 100)}%</p>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Decision
        </label>
        <select
          value={reviewForm.decision}
          onChange={e => onFormChange('decision', e.target.value)}
          className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="NEEDS_REVISION">Needs Revision</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Rating
        </label>
        <div className="flex space-x-1">{renderStars()}</div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Comment
        </label>
        <textarea
          value={reviewForm.comment}
          onChange={e => onFormChange('comment', e.target.value)}
          rows={4}
          className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="Add your review comments..."
        />
      </div>

      <div className="flex justify-end space-x-3">
        <Button variant="secondary" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
        <Button onClick={onSubmit} disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit Review'}
        </Button>
      </div>
    </div>
  );
};

export default QualityReviewForm;

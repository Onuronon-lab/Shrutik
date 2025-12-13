import React from 'react';
import { CheckCircleIcon, XCircleIcon, StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { QualityReviewItem } from '../../types/api';

interface QualityReviewsListProps {
  reviews: QualityReviewItem[];
}

const QualityReviewsList: React.FC<QualityReviewsListProps> = ({ reviews }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'APPROVED':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'REJECTED':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <StarIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'APPROVED':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
      case 'REJECTED':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300';
      default:
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300';
    }
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => {
      const isFilled = i < rating;
      return isFilled ? (
        <StarIconSolid key={i} className="h-4 w-4 text-yellow-400 dark:text-yellow-300" />
      ) : (
        <StarIcon key={i} className="h-4 w-4 text-gray-300 dark:text-gray-600" />
      );
    });
  };

  if (reviews.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircleIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No reviews yet</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Quality reviews will appear here once submitted.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {reviews.map(review => (
        <div
          key={review.id}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                {getDecisionIcon(review.decision)}
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDecisionColor(review.decision)}`}
                >
                  {review.decision}
                </span>
                <div className="flex space-x-1">{renderStars(review.rating || 0)}</div>
              </div>

              <p className="text-sm text-gray-900 dark:text-white mb-2">
                {review.transcription_text}
              </p>

              {review.comment && (
                <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg mb-2">
                  <p className="text-sm text-gray-700 dark:text-gray-300">{review.comment}</p>
                </div>
              )}

              <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                <p>Contributor: {review.contributor_name}</p>
                <p>Reviewer: {review.reviewer_name || 'System'}</p>
                <p>Reviewed: {formatDate(review.created_at)}</p>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default QualityReviewsList;

import React from 'react';
import { CheckCircleIcon, ClockIcon, ForwardIcon } from '@heroicons/react/24/solid';

interface TranscriptionProgressProps {
  currentIndex: number;
  totalCount: number;
  completedCount: number;
  skippedCount: number;
  className?: string;
}

const TranscriptionProgress: React.FC<TranscriptionProgressProps> = ({
  currentIndex,
  totalCount,
  completedCount,
  skippedCount,
  className = ''
}) => {
  const progressPercentage = totalCount > 0 ? ((currentIndex) / totalCount) * 100 : 0;
  const remainingCount = totalCount - currentIndex;

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            অগ্রগতি: {currentIndex} / {totalCount}
          </span>
          <span className="text-sm text-gray-500">
            {Math.round(progressPercentage)}% সম্পন্ন
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <CheckCircleIcon className="w-5 h-5 text-green-600 mr-1" />
            <span className="text-lg font-semibold text-green-600">
              {completedCount}
            </span>
          </div>
          <div className="text-xs text-gray-600">সম্পন্ন</div>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <ForwardIcon className="w-5 h-5 text-orange-600 mr-1" />
            <span className="text-lg font-semibold text-orange-600">
              {skippedCount}
            </span>
          </div>
          <div className="text-xs text-gray-600">এড়ানো</div>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <ClockIcon className="w-5 h-5 text-blue-600 mr-1" />
            <span className="text-lg font-semibold text-blue-600">
              {remainingCount}
            </span>
          </div>
          <div className="text-xs text-gray-600">বাকি</div>
        </div>
      </div>

      {/* Motivational Message */}
      {progressPercentage > 0 && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800 text-center">
            {progressPercentage >= 100 ? (
              <>🎉 অভিনন্দন! আপনি সব ট্রান্সক্রিপশন সম্পন্ন করেছেন!</>
            ) : progressPercentage >= 75 ? (
              <>🔥 দুর্দান্ত! আপনি প্রায় শেষের দিকে!</>
            ) : progressPercentage >= 50 ? (
              <>💪 চমৎকার! আপনি অর্ধেক পথ পার করেছেন!</>
            ) : progressPercentage >= 25 ? (
              <>⭐ ভালো কাজ চালিয়ে যান!</>
            ) : (
              <>🚀 শুরু হয়ে গেছে! চালিয়ে যান!</>
            )}
          </p>
        </div>
      )}
    </div>
  );
};

export default TranscriptionProgress;
import React, { useState, useEffect, useCallback } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { adminService } from '../../services/admin.service';
import { QualityReviewItem, FlaggedTranscription } from '../../types/api';
import { Modal } from '../ui';
import { useModal } from '../../hooks/useModal';
import { useErrorHandler } from '../../hooks/useErrorHandler';
import LoadingSpinner from '../common/LoadingSpinner';
import FlaggedTranscriptionsList from './FlaggedTranscriptionsList';
import QualityReviewsList from './QualityReviewsList';
import QualityReviewForm from './QualityReviewForm';

const QualityReview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'flagged' | 'reviews'>('flagged');
  const [flaggedTranscriptions, setFlaggedTranscriptions] = useState<FlaggedTranscription[]>([]);
  const [qualityReviews, setQualityReviews] = useState<QualityReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [playingAudio, setPlayingAudio] = useState<number | null>(null);
  const [audioElements, setAudioElements] = useState<{ [key: number]: HTMLAudioElement }>({});
  const [reviewingItem, setReviewingItem] = useState<FlaggedTranscription | null>(null);
  const [reviewForm, setReviewForm] = useState({
    decision: 'APPROVED',
    rating: 5,
    comment: '',
  });
  const [submittingReview, setSubmittingReview] = useState(false);

  const reviewModal = useModal();
  const { error, setError, handleError } = useErrorHandler();

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (activeTab === 'flagged') {
        const data = await adminService.getFlaggedTranscriptions(50);
        setFlaggedTranscriptions(data);
      } else {
        const data = await adminService.getQualityReviews(50);
        setQualityReviews(data);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, handleError, setError]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const playAudio = useCallback(
    (transcriptionId: number, audioUrl: string) => {
      // Stop any currently playing audio
      Object.values(audioElements).forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
      });

      if (!audioElements[transcriptionId]) {
        const audio = new Audio(audioUrl);
        audio.onended = () => setPlayingAudio(null);
        setAudioElements(prev => ({ ...prev, [transcriptionId]: audio }));
        audio.play();
      } else {
        audioElements[transcriptionId].play();
      }

      setPlayingAudio(transcriptionId);
    },
    [audioElements]
  );

  const stopAudio = useCallback(() => {
    if (playingAudio && audioElements[playingAudio]) {
      audioElements[playingAudio].pause();
      audioElements[playingAudio].currentTime = 0;
    }
    setPlayingAudio(null);
  }, [playingAudio, audioElements]);

  const openReviewModal = (item: FlaggedTranscription) => {
    setReviewingItem(item);
    setReviewForm({
      decision: 'APPROVED',
      rating: 5,
      comment: '',
    });
    reviewModal.open();
  };

  const closeReviewModal = () => {
    setReviewingItem(null);
    reviewModal.close();
  };

  const handleFormChange = (field: string, value: any) => {
    setReviewForm(prev => ({ ...prev, [field]: value }));
  };

  const submitReview = async () => {
    if (!reviewingItem) return;

    try {
      setSubmittingReview(true);
      // TODO: Implement submitQualityReview in adminService
      console.log('Submitting review:', {
        transcriptionId: reviewingItem.transcription_id,
        decision: reviewForm.decision,
        rating: reviewForm.rating,
        comment: reviewForm.comment,
      });

      await loadData();
      closeReviewModal();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Quality Review</h2>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">
            {typeof error === 'string' ? error : error.error}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('flagged')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'flagged'
                ? 'border-indigo-500 dark:border-indigo-400 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            Flagged Transcriptions ({flaggedTranscriptions.length})
          </button>
          <button
            onClick={() => setActiveTab('reviews')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'reviews'
                ? 'border-indigo-500 dark:border-indigo-400 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            Completed Reviews ({qualityReviews.length})
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'flagged' ? (
        <FlaggedTranscriptionsList
          transcriptions={flaggedTranscriptions}
          playingAudio={playingAudio}
          onPlayAudio={id => {
            const item = flaggedTranscriptions.find(t => t.transcription_id === id);
            if (item) playAudio(id, item.chunk_file_path);
          }}
          onStopAudio={stopAudio}
          onReview={openReviewModal}
        />
      ) : (
        <QualityReviewsList reviews={qualityReviews} />
      )}

      {/* Review Modal */}
      <Modal isOpen={reviewModal.isOpen} onClose={closeReviewModal} title="Quality Review">
        {reviewingItem && (
          <QualityReviewForm
            reviewingItem={reviewingItem}
            reviewForm={reviewForm}
            submitting={submittingReview}
            onFormChange={handleFormChange}
            onSubmit={submitReview}
            onCancel={closeReviewModal}
          />
        )}
      </Modal>
    </div>
  );
};

export default QualityReview;

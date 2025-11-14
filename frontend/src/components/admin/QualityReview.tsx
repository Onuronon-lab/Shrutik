import React, { useState, useEffect, useCallback } from 'react';
import { 
  ExclamationTriangleIcon, 
  PlayIcon, 
  PauseIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  StarIcon,
  ChatBubbleLeftIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { apiService } from '../../services/api';
import { QualityReviewItem, FlaggedTranscription } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';

const QualityReview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'flagged' | 'reviews'>('flagged');
  const [flaggedTranscriptions, setFlaggedTranscriptions] = useState<FlaggedTranscription[]>([]);
  const [qualityReviews, setQualityReviews] = useState<QualityReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playingAudio, setPlayingAudio] = useState<number | null>(null);
  const [audioElements, setAudioElements] = useState<{ [key: number]: HTMLAudioElement }>({});
  const [reviewingItem, setReviewingItem] = useState<FlaggedTranscription | null>(null);
  const [reviewForm, setReviewForm] = useState({
    decision: 'APPROVED',
    rating: 5,
    comment: ''
  });
  const [submittingReview, setSubmittingReview] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (activeTab === 'flagged') {
        const data = await apiService.getFlaggedTranscriptions(50);
        setFlaggedTranscriptions(data);
      } else {
        const data = await apiService.getQualityReviews(50);
        setQualityReviews(data);
      }
    } catch (err) {
      console.error('Failed to load quality review data:', err);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const playAudio = async (chunkId: number, filePath: string) => {
    try {
      // Stop any currently playing audio
      if (playingAudio && audioElements[playingAudio]) {
        audioElements[playingAudio].pause();
        audioElements[playingAudio].currentTime = 0;
      }

      if (playingAudio === chunkId) {
        setPlayingAudio(null);
        return;
      }

      // Get or create audio element
      let audio = audioElements[chunkId];
      if (!audio) {
        const audioUrl = await apiService.getChunkAudio(chunkId);
        audio = new Audio(audioUrl);
        audio.addEventListener('ended', () => setPlayingAudio(null));
        setAudioElements(prev => ({ ...prev, [chunkId]: audio }));
      }

      audio.play();
      setPlayingAudio(chunkId);
    } catch (err) {
      console.error('Failed to play audio:', err);
      setError('Failed to play audio. Please try again.');
    }
  };

  const submitReview = async () => {
    if (!reviewingItem) return;

    try {
      setSubmittingReview(true);
      setError(null);

      await apiService.createQualityReview(
        reviewingItem.transcription_id,
        reviewForm.decision,
        reviewForm.rating,
        reviewForm.comment || undefined
      );

      // Remove the reviewed item from the flagged list
      setFlaggedTranscriptions(prev => 
        prev.filter(item => item.transcription_id !== reviewingItem.transcription_id)
      );

      // Reset form and close modal
      setReviewingItem(null);
      setReviewForm({
        decision: 'APPROVED',
        rating: 5,
        comment: ''
      });
    } catch (err) {
      console.error('Failed to submit review:', err);
      setError('Failed to submit review. Please try again.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'APPROVED':
        return 'bg-green-100 text-green-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      case 'NEEDS_REVISION':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderStarRating = (rating: number, interactive = false, onChange?: (rating: number) => void) => {
    return (
      <div className="flex space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => interactive && onChange && onChange(star)}
            className={`${interactive ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-transform`}
            disabled={!interactive}
          >
            {star <= rating ? (
              <StarIconSolid className="h-5 w-5 text-warning-foreground" />
            ) : (
              <StarIcon className="h-5 w-5 text-muted-foreground" />
            )}
          </button>
        ))}
      </div>
    );
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
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ExclamationTriangleIcon className="h-8 w-8 text-warning" />
          <h2 className="text-2xl font-bold text-foreground">Quality Review</h2>
        </div>
        <button
          onClick={loadData}
          className="bg-warning text-warning-foreground px-4 py-2 rounded-lg hover:bg-warning-hover transition-colors"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-destructive border border-destructive-border rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="h-5 w-5 text-destructive-foreground mr-2" />
            <p className="text-destructive-foreground">{error}</p>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-border">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('flagged')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'flagged'
                ? 'border-warning-border text-warning-foreground'
                : 'border-transparent text-secondary-foreground hover:text-warning hover:border-warning-border'
            }`}
          >
            Flagged Transcriptions ({flaggedTranscriptions.length})
          </button>
          <button
            onClick={() => setActiveTab('reviews')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'reviews'
                ? 'border-warning-border text-warning-foreground'
                : 'border-transparent text-secondary-foreground hover:text-warning hover:border-warning-border'
            }`}
          >
            Completed Reviews ({qualityReviews.length})
          </button>
        </nav>
      </div>

      {/* Flagged Transcriptions Tab */}
      {activeTab === 'flagged' && (
        <div className="space-y-4">
          {flaggedTranscriptions.length === 0 ? (
            <div className="text-center py-12 bg-card rounded-lg shadow-md border border-border">
              <CheckCircleIcon className="mx-auto h-12 w-12 text-success" />
              <h3 className="mt-2 text-sm font-medium text-foreground">No flagged transcriptions</h3>
              <p className="mt-1 text-sm text-secondary-foreground">
                All transcriptions are meeting quality standards.
              </p>
            </div>
          ) : (
            flaggedTranscriptions.map((item) => (
              <div key={item.transcription_id} className="bg-card rounded-lg shadow-md border border-border p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-medium text-foreground">
                        Transcription #{item.transcription_id}
                      </h3>
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-destructive text-destructive-foreground">
                        Quality Score: {item.quality_score.toFixed(2)}
                      </span>
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-warning text-warning-foreground">
                        Confidence: {item.confidence_score.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-sm text-secondary-foreground mb-2">
                      By: {item.contributor_name} • {formatDate(item.created_at)} • {item.review_count} reviews
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => playAudio(item.chunk_id, item.chunk_file_path)}
                      className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary-hover transition-colors"
                    >
                      {playingAudio === item.chunk_id ? (
                        <PauseIcon className="h-5 w-5" />
                      ) : (
                        <PlayIcon className="h-5 w-5" />
                      )}
                    </button>
                    <button
                      onClick={() => setReviewingItem(item)}
                      className="px-4 py-2 bg-warning text-warning-foreground rounded-lg hover:bg-warning-hover transition-colors"
                    >
                      Review
                    </button>
                  </div>
                </div>
                
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-foreground font-medium mb-1">Transcription:</p>
                  <p className="text-muted-foreground">{item.text}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Quality Reviews Tab */}
      {activeTab === 'reviews' && (
        <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-card">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Transcription
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Contributor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Decision
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Rating
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Reviewer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-card divide-y divide-border">
                {qualityReviews.map((review) => (
                  <tr key={review.id} className="hover:bg-background">
                    <td className="px-6 py-4">
                      <div className="text-sm text-foreground">
                        <p className="line-clamp-2">{review.transcription_text}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                      {review.contributor_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDecisionColor(review.decision)}`}>
                        {review.decision.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {review.rating ? renderStarRating(review.rating) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {review.reviewer_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-foreground">
                      {formatDate(review.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {qualityReviews.length === 0 && (
            <div className="text-center py-12">
              <ChatBubbleLeftIcon className="mx-auto h-12 w-12 text-accent" />
              <h3 className="mt-2 text-sm font-medium text-foreground">No reviews yet</h3>
              <p className="mt-1 text-sm text-secondary-foreground">
                Quality reviews will appear here once they are completed.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Review Modal */}
      {reviewingItem && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-card">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-foreground mb-4">
                Review Transcription #{reviewingItem.transcription_id}
              </h3>
              
              <div className="space-y-4">
                <div className="bg-background rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-sm text-secondary-foreground">
                      By: {reviewingItem.contributor_name} • {formatDate(reviewingItem.created_at)}
                    </p>
                    <button
                      onClick={() => playAudio(reviewingItem.chunk_id, reviewingItem.chunk_file_path)}
                      className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary-hover transition-colors"
                    >
                      {playingAudio === reviewingItem.chunk_id ? (
                        <PauseIcon className="h-5 w-5" />
                      ) : (
                        <PlayIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                  <p className="text-foreground font-medium mb-1">Transcription:</p>
                  <p className="text-secondary-foreground">{reviewingItem.text}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-2">
                    Decision
                  </label>
                  <select
                    value={reviewForm.decision}
                    onChange={(e) => setReviewForm({ ...reviewForm, decision: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                  >
                    <option value="APPROVED">Approved</option>
                    <option value="REJECTED">Rejected</option>
                    <option value="NEEDS_REVISION">Needs Revision</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-2">
                    Rating
                  </label>
                  {renderStarRating(reviewForm.rating, true, (rating) => 
                    setReviewForm({ ...reviewForm, rating })
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-2">
                    Comment (Optional)
                  </label>
                  <textarea
                    value={reviewForm.comment}
                    onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                    placeholder="Add any additional comments..."
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    onClick={() => {
                      setReviewingItem(null);
                      setReviewForm({ decision: 'APPROVED', rating: 5, comment: '' });
                    }}
                    className="px-4 py-2 text-secondary border border-border rounded-lg hover:bg-secondary-hover transition-colors"
                    disabled={submittingReview}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitReview}
                    disabled={submittingReview}
                    className="px-4 py-2 bg-warning text-warning-foreground rounded-lg hover:bg-warning-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {submittingReview && <LoadingSpinner size="sm" className="mr-2" />}
                    Submit Review
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QualityReview;
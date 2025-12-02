import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { AudioChunk, TranscriptionSubmission } from '../../types/api';
import AudioPlayer from './AudioPlayer';
import TranscriptionForm from './TranscriptionForm';
import TranscriptionProgress from './TranscriptionProgress';
import { ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';

interface TranscriptionInterfaceProps {
  selectedQuantity: number;
  onComplete: () => void;
  onBack: () => void;
  className?: string;
}

const TranscriptionInterface: React.FC<TranscriptionInterfaceProps> = ({
  selectedQuantity,
  onComplete,
  onBack,
  className = '',
}) => {
  const [chunks, setChunks] = useState<AudioChunk[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);
  const [skippedCount, setSkippedCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const { t } = useTranslation();

  const currentChunk = chunks[currentIndex];

  useEffect(() => {
    loadChunks();
  }, [selectedQuantity]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (currentChunk) {
      loadAudioForChunk(currentChunk.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChunk]);

  const loadChunks = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.getRandomChunks(selectedQuantity);

      if (response.chunks && response.chunks.length > 0) {
        setChunks(response.chunks);
        setSessionId(response.session_id);
        setCurrentIndex(0);
        setCompletedCount(0);
        setSkippedCount(0);
        setSessionComplete(false);
      } else {
        setError(t('transcription-error-no-chunks'));
      }
    } catch (err: any) {
      console.error('Error loading chunks:', err);
      setError(t('transcription-error-load-chunks'));
    } finally {
      setIsLoading(false);
    }
  };

  const loadAudioForChunk = async (chunkId: number) => {
    try {
      const audioUrl = await apiService.getChunkAudio(chunkId);
      setAudioUrl(audioUrl);
    } catch (err: any) {
      console.error('Error loading audio:', err);
      setError(t('transcription-error-load-audio'));
    }
  };

  const handleTranscriptionSubmit = async (text: string) => {
    if (!currentChunk) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const submission: TranscriptionSubmission = {
        session_id: sessionId || 'default-session',
        transcriptions: [
          {
            chunk_id: currentChunk.id,
            text: text,
            language_id: 1, // Assuming Bangla language ID is 1
          },
        ],
        skipped_chunk_ids: [],
      };

      await apiService.submitTranscription(submission);

      setCompletedCount(prev => prev + 1);
      moveToNext();
    } catch (err: any) {
      console.error('Error submitting transcription:', err);

      // If session is invalid, try to reload chunks to get a new session
      if (err.response?.data?.detail?.includes('session')) {
        setError(t('transcription-error-session-expired'));
        await loadChunks();
        return;
      }

      setError(t('transcription-error-submit'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = async () => {
    if (!currentChunk) return;

    try {
      setIsSubmitting(true);
      await apiService.skipChunk(currentChunk.id);

      setSkippedCount(prev => prev + 1);
      moveToNext();
    } catch (err: any) {
      console.error('Error skipping chunk:', err);
      // Continue anyway since skip is not critical
      setSkippedCount(prev => prev + 1);
      moveToNext();
    } finally {
      setIsSubmitting(false);
    }
  };

  const moveToNext = () => {
    if (currentIndex + 1 >= chunks.length) {
      // Session complete
      setSessionComplete(true);
    } else {
      setCurrentIndex(prev => prev + 1);
    }
  };

  const handleStartNewSession = () => {
    setSessionComplete(false);
    loadChunks();
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">{t('transcription-loading-chunks')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center mb-4">
          <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mr-2" />
          <h3 className="text-lg font-semibold text-red-800">{t('transcription-error-title')}</h3>
        </div>
        <p className="text-red-700 mb-4">{error}</p>
        <div className="flex space-x-3">
          <button
            onClick={loadChunks}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
          >
            {t('transcription-try-again')}
          </button>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          >
            {t('transcription-go-back')}
          </button>
        </div>
      </div>
    );
  }

  if (sessionComplete) {
    return (
      <div
        className={`bg-green-50 border border-green-200 rounded-lg p-8 text-center ${className}`}
      >
        <CheckCircleIcon className="w-16 h-16 text-green-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-green-800 mb-4">
          {t('transcription-session-complete-title')}
        </h2>

        <div className="bg-white rounded-lg p-6 mb-6 inline-block">
          <div className="grid grid-cols-2 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-green-600 mb-1">{completedCount}</div>
              <div className="text-sm text-gray-600">{t('transcription-session-completed')}</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-600 mb-1">{skippedCount}</div>
              <div className="text-sm text-gray-600">{t('transcription-session-skipped')}</div>
            </div>
          </div>
        </div>

        <p className="text-green-700 mb-6">{t('transcription-session-thanks')}</p>

        <div className="flex justify-center space-x-4">
          <button
            onClick={handleStartNewSession}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
          >
            {t('transcription-do-more')}
          </button>
          <button
            onClick={onComplete}
            className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          >
            {t('transcription-finish')}
          </button>
        </div>
      </div>
    );
  }

  if (!currentChunk || !audioUrl) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">{t('transcription-loading-audio')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Progress */}
      <TranscriptionProgress
        currentIndex={currentIndex}
        totalCount={chunks.length}
        completedCount={completedCount}
        skippedCount={skippedCount}
      />

      {/* Current Chunk Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-semibold text-blue-800">চাঙ্ক #{currentIndex + 1}</h3>
            <p className="text-sm text-blue-600">
              {t('transcription-chunk-duration')} {currentChunk.duration.toFixed(1)} {t('seconds')}
            </p>
          </div>
          <button
            onClick={onBack}
            className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 rounded transition-colors"
          >
            {t('transcription-go-back')}
          </button>
        </div>
      </div>

      {/* Audio Player */}
      <AudioPlayer
        audioUrl={audioUrl}
        onLoadError={error => setError(t('transcription-error', { err: error }))}
      />

      {/* Transcription Form */}
      <TranscriptionForm
        chunkId={currentChunk.id}
        onSubmit={handleTranscriptionSubmit}
        onSkip={handleSkip}
        isSubmitting={isSubmitting}
      />
    </div>
  );
};

export default TranscriptionInterface;

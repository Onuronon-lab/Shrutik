import React, { useState } from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import QuantitySelector from '../components/transcription/QuantitySelector';
import TranscriptionInterface from '../components/transcription/TranscriptionInterface';
import { useTranslation } from 'react-i18next';

const TranscribePage: React.FC = () => {
  const [selectedQuantity, setSelectedQuantity] = useState<number>(0);
  const [sessionStarted, setSessionStarted] = useState(false);

  const { t } = useTranslation();

  const handleQuantityChange = (quantity: number) => {
    setSelectedQuantity(quantity);
  };

  const handleStartSession = () => {
    if (selectedQuantity > 0) {
      setSessionStarted(true);
    }
  };

  const handleSessionComplete = () => {
    setSessionStarted(false);
    setSelectedQuantity(0);
  };

  const handleBackToSelection = () => {
    setSessionStarted(false);
  };

  if (sessionStarted) {
    return (
      <div className="max-w-4xl mx-auto">
        <TranscriptionInterface
          selectedQuantity={selectedQuantity}
          onComplete={handleSessionComplete}
          onBack={handleBackToSelection}
        />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <DocumentTextIcon className="mx-auto h-16 w-16 text-success mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-2">{t('transcriptionPage-title')}</h1>
        <p className="text-secondary-foreground">
          {t('transcriptionPage-description')}
        </p>
      </div>

      <div className="space-y-6">
        {/* Quantity Selection */}
        <QuantitySelector
          selectedQuantity={selectedQuantity}
          onQuantityChange={handleQuantityChange}
        />

        {/* Start Button */}
        {selectedQuantity > 0 && (
          <div className="text-center">
            <button
              onClick={handleStartSession}
              className="px-8 py-3 bg-success hover:bg-success-hover text-success-foreground text-lg font-semibold rounded-lg transition-colors shadow-md hover:shadow-lg"
            >
              {t('transcriptionPage-start')}
            </button>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-info border border-info-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-info-foreground mb-4">{t('transcriptionPage-instruction')}</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-info-foreground">
            <div>
              <h4 className="font-medium mb-2">{t('transcriptionPage-audio-instructions')}</h4>
              <ul className="space-y-1 text-xs">
                <li>{t('transcriptionPage-audio-play')}</li>
                <li>{t('transcriptionPage-audio-waveform')}</li>
                <li>{t('transcriptionPage-audio-restart')}</li>
                <li>{t('transcriptionPage-audio-repeat')}</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">{t('transcriptionPage-writing-instructions')}</h4>
              <ul className="space-y-1 text-xs">
                <li>{t('transcriptionPage-write-accurately')}</li>
                <li>{t('transcriptionPage-use-keyboard')}</li>
                <li>{t('transcriptionPage-avoid-unclear-audio')}</li>
                <li>{t('transcriptionPage-submit-shortcut')}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscribePage;
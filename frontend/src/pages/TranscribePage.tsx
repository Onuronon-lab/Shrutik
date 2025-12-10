import React, { useState } from 'react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import QuantitySelector from '../components/transcription/QuantitySelector';
import TranscriptionInterface from '../components/transcription/TranscriptionInterface';
import { useTranslation } from 'react-i18next';

const TranscribePage: React.FC = () => {
  const [selectedQuantity, setSelectedQuantity] = useState<number>(0);
  const [sessionStarted, setSessionStarted] = useState(false);

  const { t } = useTranslation();

  const formatInstruction = (key: string) => t(key).replace(/^•\s*/, '').trim();

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
        <p className="text-secondary-foreground">{t('transcriptionPage-description')}</p>
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
        <div className="relative overflow-hidden rounded-2xl border border-border bg-card/90 dark:bg-muted/40 p-6 shadow-[0_12px_45px_rgba(15,23,42,0.18)] backdrop-blur">
          <div className="pointer-events-none absolute inset-0 opacity-80 dark:opacity-40">
            <div className="absolute -top-24 -right-16 h-48 w-48 rounded-full bg-primary/20 blur-3xl" />
            <div className="absolute -bottom-16 -left-10 h-40 w-40 rounded-full bg-violet-400/20 blur-3xl" />
          </div>
          <div className="relative flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            <div className="h-8 w-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center ring-1 ring-primary/20">
              ℹ️
            </div>
            <span>{t('transcriptionPage-instruction')}</span>
          </div>
          <h3 className="relative text-2xl font-semibold text-foreground mb-6 mt-3">
            {t('transcriptionPage-instruction')}
          </h3>
          <div className="relative grid gap-6 md:grid-cols-2 text-sm text-secondary-foreground">
            <div className="rounded-xl border border-border bg-card/80 dark:bg-muted/60 p-5 shadow-sm">
              <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                {t('transcriptionPage-audio-instructions')}
              </h4>
              <ul className="space-y-2 text-xs leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-primary/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-audio-play')}
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-audio-waveform')}
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-audio-restart')}
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-audio-repeat')}
                </li>
              </ul>
            </div>
            <div className="rounded-xl border border-border bg-card/80 dark:bg-muted/60 p-5 shadow-sm">
              <h4 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                {t('transcriptionPage-writing-instructions')}
              </h4>
              <ul className="space-y-2 text-xs leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-violet-500/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-write-accurately')}
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-violet-500/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-use-keyboard')}
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-violet-500/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-avoid-unclear-audio')}
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-violet-500/80 text-base leading-none">•</span>
                  {formatInstruction('transcriptionPage-submit-shortcut')}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscribePage;

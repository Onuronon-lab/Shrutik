import React from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import { StrictDurationOption } from '../../types/enhanced';

// Re-export for backward compatibility
export type DurationOption = StrictDurationOption;

// Legacy interface for backward compatibility
interface LegacyDurationSelectorProps {
  onDurationSelect: (duration: DurationOption) => void;
  className?: string;
  'data-testid'?: string;
}

const DurationSelector: React.FC<LegacyDurationSelectorProps> = ({
  onDurationSelect,
  className = '',
  'data-testid': testId,
}) => {
  const { t } = useTranslation();

  const DURATION_OPTIONS: DurationOption[] = [
    {
      value: '2_minutes',
      label: t('recordPage-2-minutes'),
      minutes: 2,
      description: t('recordPage-quick-record-session'),
      maxFileSize: 10 * 1024 * 1024, // 10MB
      recommendedFor: ['quick-test', 'voice-sample'],
    },
    {
      value: '5_minutes',
      label: t('recordPage-5-minutes'),
      minutes: 5,
      description: t('recordPage-standard-record-session'),
      maxFileSize: 25 * 1024 * 1024, // 25MB
      recommendedFor: ['standard-recording', 'speech-sample'],
    },
    {
      value: '10_minutes',
      label: t('recordPage-10-minutes'),
      minutes: 10,
      description: t('recordPage-extended-record-session'),
      maxFileSize: 50 * 1024 * 1024, // 50MB
      recommendedFor: ['extended-recording', 'detailed-speech'],
    },
  ];

  return (
    <div
      className={`bg-card rounded-lg shadow-md p-6 border border-border ${className}`}
      data-testid={testId}
    >
      <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center">
        <ClockIcon className="w-5 h-5 mr-2" />
        {t('recordPage-selection-record-duration')}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {DURATION_OPTIONS.map(option => (
          <button
            key={option.value}
            onClick={() => onDurationSelect(option)}
            className="p-4 border-2 border-border rounded-lg hover:border-primary hover:bg-nutral transition-all duration-200 text-left"
            data-testid={`duration-option-${option.value}`}
          >
            <div className="font-semibold text-foreground">{option.label}</div>
            <div className="text-sm text-secondary-foreground mt-1">{option.description}</div>
            <div className="text-xs text-secondary-foreground mt-2">
              Max file size: {Math.round(option.maxFileSize / (1024 * 1024))}MB
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default DurationSelector;

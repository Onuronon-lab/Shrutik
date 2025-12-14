import { useCallback, useMemo } from 'react';
import { useScriptStore } from '../stores/scriptStore';
import { DurationOption } from '../types/state';
import { StrictDurationOption } from '../types/enhanced';
import { useTranslation } from 'react-i18next';

export interface UseDurationSelectorReturn {
  // State
  selectedDuration: DurationOption | null;
  availableOptions: DurationOption[];

  // Actions
  selectDuration: (duration: DurationOption) => void;
  clearSelection: () => void;

  // Validation
  isValidDuration: (duration: DurationOption | null) => boolean;
  validateSelection: (duration: DurationOption | null) => string | null;

  // Computed values
  hasSelection: boolean;
  selectedMinutes: number;
  selectedSeconds: number;
  maxRecordingTime: number; // in seconds
}

export function useDurationSelector(): UseDurationSelectorReturn {
  const { t } = useTranslation();
  const { selectedDuration, setSelectedDuration } = useScriptStore();

  // Available duration options
  const availableOptions: StrictDurationOption[] = useMemo(
    () => [
      {
        value: '2_minutes',
        label: t('recordPage-2-minutes'),
        minutes: 2,
        description: t('recordPage-quick-record-session'),
        maxFileSize: 10 * 1024 * 1024, // 10MB
        recommendedFor: ['Quick practice', 'Short phrases'],
      },
      {
        value: '5_minutes',
        label: t('recordPage-5-minutes'),
        minutes: 5,
        description: t('recordPage-standard-record-session'),
        maxFileSize: 25 * 1024 * 1024, // 25MB
        recommendedFor: ['Standard recording', 'Paragraphs'],
      },
      {
        value: '10_minutes',
        label: t('recordPage-10-minutes'),
        minutes: 10,
        description: t('recordPage-extended-record-session'),
        maxFileSize: 50 * 1024 * 1024, // 50MB
        recommendedFor: ['Long content', 'Multiple paragraphs'],
      },
    ],
    [t]
  );

  // Select duration
  const selectDuration = useCallback(
    (duration: DurationOption) => {
      if (isValidDuration(duration)) {
        setSelectedDuration(duration);
      } else {
        console.warn('Invalid duration option:', duration);
      }
    },
    [setSelectedDuration]
  );

  // Clear selection
  const clearSelection = useCallback(() => {
    setSelectedDuration(null);
  }, [setSelectedDuration]);

  // Validate duration option
  const isValidDuration = useCallback(
    (duration: DurationOption | null): boolean => {
      if (!duration) return false;

      return availableOptions.some(
        option =>
          option.value === duration.value &&
          option.minutes === duration.minutes &&
          option.minutes > 0 &&
          option.minutes <= 60 // Max 1 hour
      );
    },
    [availableOptions]
  );

  // Validate selection and return error message if invalid
  const validateSelection = useCallback(
    (duration: DurationOption | null): string | null => {
      if (!duration) {
        return 'Please select a recording duration';
      }

      if (!isValidDuration(duration)) {
        return 'Invalid duration selection';
      }

      if (duration.minutes < 1) {
        return 'Duration must be at least 1 minute';
      }

      if (duration.minutes > 60) {
        return 'Duration cannot exceed 60 minutes';
      }

      return null; // Valid
    },
    [isValidDuration]
  );

  // Computed values
  const hasSelection = selectedDuration !== null;
  const selectedMinutes = selectedDuration?.minutes || 0;
  const selectedSeconds = selectedMinutes * 60;
  const maxRecordingTime = selectedSeconds;

  return {
    // State
    selectedDuration,
    availableOptions,

    // Actions
    selectDuration,
    clearSelection,

    // Validation
    isValidDuration,
    validateSelection,

    // Computed values
    hasSelection,
    selectedMinutes,
    selectedSeconds,
    maxRecordingTime,
  };
}

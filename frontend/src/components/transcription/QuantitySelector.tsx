import React from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import { count } from 'console';

interface QuantitySelectorProps {
  selectedQuantity: number;
  onQuantityChange: (quantity: number) => void;
  disabled?: boolean;
  className?: string;
}

const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  selectedQuantity,
  onQuantityChange,
  disabled = false,
  className = '',
}) => {
  const { t } = useTranslation();
  const quantities = [
    {
      value: 2,
      label: t('transcriptionPage-2-sentences'),
      time: t('transcriptionPage-approx-5-min'),
      color: 'bg-success text-success-foreground border-success-border',
    },
    {
      value: 5,
      label: t('transcriptionPage-5-sentences'),
      time: t('transcriptionPage-approx-10-min'),
      color: 'bg-primary text-primary-foreground border-primary-border',
    },
    {
      value: 10,
      label: t('transcriptionPage-10-sentences'),
      time: t('transcriptionPage-approx-20-min'),
      color: 'bg-info text-info-foreground border-info-border',
    },
    {
      value: 15,
      label: t('transcriptionPage-15-sentences'),
      time: t('transcriptionPage-approx-30-min'),
      color: 'bg-warning text-warning-foreground border-warning-border',
    },
    {
      value: 20,
      label: t('transcriptionPage-20-sentences'),
      time: t('transcriptionPage-approx-40-min'),
      color: 'bg-destructive text-destructive-foreground border-destructive-border',
    },
  ];

  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">
          {t('transcriptionPage-how-many-sentences')}
        </h3>
        <p className="text-secondary-foreground text-sm">{t('transcriptionPage-select-amount')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {quantities.map(option => (
          <button
            key={option.value}
            onClick={() => onQuantityChange(option.value)}
            disabled={disabled}
            className={`
              relative p-4 rounded-lg border-2 transition-all duration-200 text-center
              ${
                selectedQuantity === option.value
                  ? `${option.color} border-current shadow-md transform scale-105`
                  : 'bg-background text-foreground border-border hover:bg-card hover:border-accent hover:shadow-sm hover:transform hover:scale-105'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-sm'}
            `}
          >
            {/* Selection Indicator */}
            {selectedQuantity === option.value && (
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-success text-success-foreground rounded-full flex items-center justify-center">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}

            <div className="space-y-2">
              <div className="text-2xl font-bold">{option.value}</div>
              <div className="text-sm font-medium">{option.label}</div>
              <div className="flex items-center justify-center text-xs opacity-75">
                <ClockIcon className="w-3 h-3 mr-1" />
                {option.time}
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedQuantity > 0 && (
        <div className="mt-6 p-4 bg-primary border border-primary-border rounded-lg">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg
                className="w-5 h-5 text-primary-foreground mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="text-sm text-primary-foreground">
              <p className="font-medium mb-1">
                {t('quantitySelector-selected', { count: selectedQuantity })}{' '}
              </p>
              <ul className="text-xs space-y-1 opacity-90">
                <li>{t('quantitySelector-tip-1')}</li>
                <li>{t('quantitySelector-tip-2')}</li>
                <li>{t('quantitySelector-tip-3')}</li>
                <li>{t('quantitySelector-tip-4')}</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuantitySelector;

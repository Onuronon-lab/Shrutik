import React from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import { Button } from '../../../../components/ui';

interface BatchHeaderProps {
  t: TFunction<'translation'>;
  onCreateClick: () => void;
}

export const BatchHeader: React.FC<BatchHeaderProps> = ({ t, onCreateClick }) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">{t('export.title')}</h1>
          <p className="text-secondary-foreground">{t('export.subtitle')}</p>
        </div>
        <Button
          onClick={onCreateClick}
          variant="primary"
          className="relative group overflow-hidden rounded-2xl border border-white/5 bg-gradient-to-r from-primary to-violet-500 px-6 py-3 text-white shadow-[0_20px_45px_rgba(124,58,237,0.35)] transition-all hover:shadow-[0_30px_60px_rgba(124,58,237,0.45)] hover:-translate-y-0.5"
        >
          <span className="flex items-center gap-3 text-base font-semibold">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20 text-white backdrop-blur">
              <PlusIcon className="h-4 w-4" />
            </span>
            <span>{t('export.create_batch')}</span>
          </span>
        </Button>
      </div>
    </div>
  );
};

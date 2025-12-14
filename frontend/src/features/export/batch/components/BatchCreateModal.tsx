import React from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import { Modal, Button } from '../../../../components/ui';
import type { CreateBatchFormValues } from '../types';

interface BatchCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  values: CreateBatchFormValues;
  onChange: (next: Partial<CreateBatchFormValues>) => void;
  onSubmit: () => Promise<void>;
  loading: boolean;
  t: TFunction<'translation'>;
}

export const BatchCreateModal: React.FC<BatchCreateModalProps> = ({
  isOpen,
  onClose,
  values,
  onChange,
  onSubmit,
  loading,
  t,
}) => {
  const handleInputChange =
    (field: keyof CreateBatchFormValues) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = field === 'force_create' ? event.target.checked : event.target.value;
      onChange({ [field]: value });
    };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t('export.modal.title')} size="md">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-secondary-foreground mb-2">
            {t('export.modal.date_range')}
          </label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="date"
              value={values.date_from}
              onChange={handleInputChange('date_from')}
              className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
              placeholder={t('export.modal.date_from')}
            />
            <input
              type="date"
              value={values.date_to}
              onChange={handleInputChange('date_to')}
              className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
              placeholder={t('export.modal.date_to')}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-secondary-foreground mb-2">
            {t('export.modal.duration_range')}
          </label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              step="0.1"
              value={values.min_duration}
              onChange={handleInputChange('min_duration')}
              className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
              placeholder={t('export.modal.duration_min')}
            />
            <input
              type="number"
              step="0.1"
              value={values.max_duration}
              onChange={handleInputChange('max_duration')}
              className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring"
              placeholder={t('export.modal.duration_max')}
            />
          </div>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="force_create"
            checked={values.force_create}
            onChange={handleInputChange('force_create')}
            className="h-4 w-4 text-primary focus:ring-ring border-border rounded"
          />
          <label htmlFor="force_create" className="ml-2 text-sm text-secondary-foreground">
            {t('export.modal.force_create')}
          </label>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex">
            <InformationCircleIcon className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0" />
            <p className="text-xs text-blue-800">{t('export.modal.info')}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 flex space-x-3">
        <Button onClick={onClose} variant="outline" fullWidth>
          {t('export.modal.cancel')}
        </Button>
        <Button
          onClick={onSubmit}
          disabled={loading}
          variant="primary"
          fullWidth
          isLoading={loading}
        >
          {loading
            ? t('export.modal.create_in_progress', { defaultValue: 'Creating...' })
            : t('export.modal.create')}
        </Button>
      </div>
    </Modal>
  );
};

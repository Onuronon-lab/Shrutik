import React from 'react';
import { ArrowDownTrayIcon, CheckCircleIcon, PlusIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import { Modal, Button } from '../../../../components/ui';
import type { ExportBatch } from '../types';
import { formatFileSize } from '../utils';

interface BatchSuccessModalProps {
  isOpen: boolean;
  onClose: () => void;
  batch: ExportBatch | null;
  onDownload: (batchId: string) => void;
  onCreateAnother: () => void;
  canDownload: boolean;
  downloadDisabledReason?: string | undefined;
  t: TFunction<'translation'>;
}

export const BatchSuccessModal: React.FC<BatchSuccessModalProps> = ({
  isOpen,
  onClose,
  batch,
  onDownload,
  onCreateAnother,
  canDownload,
  downloadDisabledReason,
  t,
}) => {
  if (!batch) return null;

  const handleDownload = () => {
    onDownload(batch.batch_id);
    onClose();
  };

  const handleCreateAnother = () => {
    onCreateAnother();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t('export.success.modal.title')} size="lg">
      <div className="text-center">
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-success/10 mb-4">
          <CheckCircleIcon className="h-6 w-6 text-success" />
        </div>

        <h3 className="text-lg font-medium text-foreground mb-2">
          {t('export.success.modal.batch_created')}
        </h3>

        <p className="text-sm text-secondary-foreground mb-6">
          {t('export.success.modal.description')}
        </p>

        {/* Batch Details */}
        <div className="bg-accent rounded-lg p-4 mb-6 text-left">
          <h4 className="font-medium text-foreground mb-3">
            {t('export.success.modal.batch_details')}
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-secondary-foreground">
                {t('export.success.modal.batch_id')}:
              </span>
              <span className="font-mono text-foreground">{batch.batch_id.substring(0, 8)}...</span>
            </div>
            <div className="flex justify-between">
              <span className="text-secondary-foreground">
                {t('export.success.modal.chunk_count')}:
              </span>
              <span className="text-foreground">
                {batch.chunk_count} {t('export.success.modal.chunks')}
              </span>
            </div>
            {batch.file_size_bytes && (
              <div className="flex justify-between">
                <span className="text-secondary-foreground">
                  {t('export.success.modal.file_size')}:
                </span>
                <span className="text-foreground">{formatFileSize(batch.file_size_bytes)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-secondary-foreground">{t('export.success.modal.status')}:</span>
              <span className="text-foreground capitalize">{batch.status}</span>
            </div>
            {batch.filter_criteria && Object.keys(batch.filter_criteria).length > 0 && (
              <div className="mt-3 pt-3 border-t border-border">
                <span className="text-secondary-foreground text-xs">
                  {t('export.success.modal.filters_applied')}:
                </span>
                <div className="mt-1 text-xs text-secondary-foreground">
                  {Object.entries(batch.filter_criteria).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span>{key}:</span>
                      <span>{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Download Status */}
        {batch.status === 'completed' ? (
          <div className="mb-6">
            {canDownload ? (
              <div className="bg-success/10 border border-success/20 rounded-lg p-3 mb-4">
                <p className="text-sm text-success">
                  {t('export.success.modal.ready_to_download')}
                </p>
              </div>
            ) : (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 mb-4">
                <p className="text-sm text-destructive">
                  {downloadDisabledReason || t('export.success.modal.download_unavailable')}
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
            <p className="text-sm text-blue-800">
              {batch.status === 'processing'
                ? t('export.success.modal.processing_message')
                : t('export.success.modal.pending_message')}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          {batch.status === 'completed' && (
            <div className="relative">
              <Button
                onClick={handleDownload}
                disabled={!canDownload}
                variant="primary"
                className={`flex items-center justify-center ${
                  !canDownload ? 'cursor-not-allowed' : ''
                }`}
                title={
                  !canDownload ? downloadDisabledReason : t('export.tooltip.ready_to_download')
                }
              >
                <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                {t('export.success.modal.download_now')}
              </Button>
              {!canDownload && downloadDisabledReason && (
                <div className="absolute -bottom-8 left-0 right-0 text-xs text-destructive text-center">
                  {downloadDisabledReason.length > 50
                    ? `${downloadDisabledReason.substring(0, 50)}...`
                    : downloadDisabledReason}
                </div>
              )}
            </div>
          )}

          <Button
            onClick={handleCreateAnother}
            variant="outline"
            className="flex items-center justify-center"
            title={t('export.success.modal.create_another_tooltip')}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            {t('export.success.modal.create_another')}
          </Button>

          <Button
            onClick={onClose}
            variant="outline"
            title={t('export.success.modal.close_tooltip')}
          >
            {t('export.success.modal.close')}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

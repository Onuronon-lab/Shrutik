import React from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';
import LoadingSpinner from '../common/LoadingSpinner';
import { useTranslation } from 'react-i18next';

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

interface UploadManagerProps {
  hasRecording: boolean;
  uploadStatus: UploadStatus;
  uploadProgress: number;
  error: string | null;
  onUpload: () => void;
  className?: string;
  'data-testid'?: string;
}

const UploadManager: React.FC<UploadManagerProps> = ({
  hasRecording,
  uploadStatus,
  uploadProgress,
  error,
  onUpload,
  className = '',
  'data-testid': testId,
}) => {
  const { t } = useTranslation();

  if (!hasRecording) {
    return null;
  }

  return (
    <div className={`border-t pt-4 ${className}`} data-testid={testId}>
      {/* Upload Button */}
      {uploadStatus !== 'success' && (
        <button
          onClick={onUpload}
          disabled={uploadStatus === 'uploading'}
          className="w-full bg-info hover:bg-info-hover disabled:bg-muted text-info-foreground py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center"
          data-testid="upload-button"
        >
          {uploadStatus === 'uploading' ? (
            <>
              <LoadingSpinner size="sm" />
              <span className="ml-2">Uploading... {Math.round(uploadProgress)}%</span>
            </>
          ) : (
            'Upload Recording'
          )}
        </button>
      )}

      {/* Success Message */}
      {uploadStatus === 'success' && (
        <div
          className="bg-success/10 border border-success-border rounded-lg p-4 flex items-center text-success"
          data-testid="success-message"
        >
          <CheckCircleIcon className="w-5 h-5 mr-2" />
          {t('record-upload-success')}
        </div>
      )}

      {/* Error Message */}
      {error && uploadStatus === 'error' && (
        <div
          className="bg-destructive border border-destructive-border rounded-lg p-4 flex items-center text-destructive-foreground"
          data-testid="error-message"
        >
          <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
          {error}
        </div>
      )}
    </div>
  );
};

export default UploadManager;

import React from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';

interface PlatformStatsOverviewProps {
  stats?: any;
  t: TFunction<'translation'>;
}

export const PlatformStatsOverview: React.FC<PlatformStatsOverviewProps> = ({ stats, t }) => {
  if (!stats) return null;

  return (
    <div className="bg-card rounded-lg shadow-md p-6 mb-8 border border-border">
      <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
        <InformationCircleIcon className="h-6 w-6 text-primary mr-2" />
        {t('dataExport-platform-overview')}
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-foreground">
            {stats.statistics?.total_recordings || 0}
          </p>
          <p className="text-sm text-secondary-foreground">
            {t('dataExport-overview-total-record')}
          </p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-foreground">
            {stats.statistics?.total_chunks || 0}
          </p>
          <p className="text-sm text-secondary-foreground">{t('dataExport-overview-audio')}</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-foreground">
            {stats.statistics?.total_transcriptions || 0}
          </p>
          <p className="text-sm text-secondary-foreground">
            {t('dataExport-overview-transcription')}
          </p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-foreground">
            {stats.statistics?.validated_transcriptions || 0}
          </p>
          <p className="text-sm text-secondary-foreground">{t('dataExport-overview-validate')}</p>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import type { DownloadQuota } from '../types';

interface BatchQuotaCardProps {
  quota: DownloadQuota | null;
  t: TFunction<'translation'>;
}

export const BatchQuotaCard: React.FC<BatchQuotaCardProps> = ({ quota, t }) => {
  if (!quota) return null;

  const progress = Math.min(100, (quota.downloads_today / Math.max(quota.daily_limit, 1)) * 100);

  return (
    <div className="bg-card rounded-lg shadow-md p-6 mb-6 border border-border">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <ArrowDownTrayIcon className="h-8 w-8 text-primary mr-3" />
          <div>
            <h3 className="text-lg font-semibold text-foreground">{t('export.quota.title')}</h3>
            <p className="text-sm text-secondary-foreground">
              {t('export.quota.remaining', {
                remaining: quota.downloads_remaining,
                limit: quota.daily_limit,
              })}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-foreground">
            {quota.downloads_today}/{quota.daily_limit}
          </div>
          <p className="text-xs text-secondary-foreground">
            {t('export.quota.resets_at')} {new Date(quota.reset_time).toLocaleTimeString()}
          </p>
        </div>
      </div>
      <div className="mt-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { ArrowDownTrayIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import type { TFunction } from 'i18next';
import type { DownloadQuota } from '../types';

interface BatchQuotaCardProps {
  quota: DownloadQuota | null;
  userRole?: string;
  t: TFunction<'translation'>;
}

export const BatchQuotaCard: React.FC<BatchQuotaCardProps> = ({ quota, userRole, t }) => {
  // Debug logging to help troubleshoot the issue
  console.log('BatchQuotaCard Debug:', {
    quota,
    userRole,
    shouldHide: !quota || userRole === 'admin' || quota?.daily_limit === -1,
  });

  // Hide quota card for admin users (unlimited downloads)
  if (!quota || userRole === 'admin' || quota.daily_limit === -1 || quota.is_unlimited) return null;

  const progress = Math.min(100, (quota.downloads_today / Math.max(quota.daily_limit, 1)) * 100);
  const isQuotaExhausted = quota.downloads_remaining <= 0 && !quota.is_unlimited;

  // Handle null or invalid reset_time gracefully
  let resetTime: Date | null = null;
  let hoursUntilReset = 0;

  if (quota.reset_time) {
    try {
      resetTime = new Date(quota.reset_time);
      // Check if the date is valid (not 1970 or invalid)
      if (resetTime.getFullYear() > 2000) {
        const now = new Date();
        hoursUntilReset = Math.ceil((resetTime.getTime() - now.getTime()) / (1000 * 60 * 60));
      } else {
        resetTime = null;
      }
    } catch (e) {
      console.error('Invalid reset_time:', quota.reset_time, e);
      resetTime = null;
    }
  }

  return (
    <div
      className={`bg-card rounded-lg shadow-md p-6 mb-6 border ${
        isQuotaExhausted ? 'border-destructive' : 'border-border'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {isQuotaExhausted ? (
            <ExclamationTriangleIcon className="h-8 w-8 text-destructive mr-3" />
          ) : (
            <ArrowDownTrayIcon className="h-8 w-8 text-primary mr-3" />
          )}
          <div>
            <h3 className="text-lg font-semibold text-foreground">{t('export.quota.title')}</h3>
            <p className="text-sm text-secondary-foreground">
              {isQuotaExhausted ? (
                <span className="text-destructive font-medium">{t('export.quota.exhausted')}</span>
              ) : (
                t('export.quota.remaining', {
                  remaining: quota.downloads_remaining,
                  limit: quota.daily_limit,
                })
              )}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div
            className={`text-2xl font-bold ${
              isQuotaExhausted ? 'text-destructive' : 'text-foreground'
            }`}
          >
            {quota.downloads_today}/{quota.daily_limit}
          </div>
          <div className="flex items-center text-xs text-secondary-foreground mt-1">
            <ClockIcon className="h-3 w-3 mr-1" />
            <span>
              {resetTime
                ? isQuotaExhausted
                  ? t('export.quota.resets_in_hours', { hours: hoursUntilReset })
                  : `${t('export.quota.resets_at')} ${resetTime.toLocaleTimeString()}`
                : t('export.quota.no_reset_time')}
            </span>
          </div>
        </div>
      </div>
      <div className="mt-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              isQuotaExhausted ? 'bg-destructive' : 'bg-primary'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        {isQuotaExhausted && resetTime && (
          <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">
              {t('export.quota.exhausted_message', {
                resetTime: resetTime.toLocaleString(),
                hours: hoursUntilReset,
              })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

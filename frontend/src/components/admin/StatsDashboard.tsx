import React, { useState, useEffect, useCallback } from 'react';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import { adminService } from '../../services/admin.service';
import { PlatformStats, UsageAnalytics, UserStats } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';
import StatsCards from './StatsCards';
import UsageChart from './UsageChart';
import TopContributors from './TopContributors';

const StatsDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [platformStats, setPlatformStats] = useState<PlatformStats | null>(null);
  const [usageAnalytics, setUsageAnalytics] = useState<UsageAnalytics | null>(null);
  const [userStats, setUserStats] = useState<UserStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyticsRange, setAnalyticsRange] = useState(30);

  const loadAllData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, analyticsData, usersData] = await Promise.all([
        adminService.getPlatformStats(),
        adminService.getUsageAnalytics(analyticsRange),
        adminService.getUserStats(20),
      ]);

      setPlatformStats(statsData);
      setUsageAnalytics(analyticsData);
      setUserStats(usersData);
    } catch (err) {
      // Analytics loading failed, will show error state
      setError(
        t('errors.generic.server', {
          defaultValue: 'Failed to load analytics data. Please try again.',
        })
      );
    } finally {
      setLoading(false);
    }
  }, [analyticsRange]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <ChartBarIcon className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Platform Statistics</h2>
      </div>

      {platformStats && <StatsCards stats={platformStats} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {usageAnalytics && (
          <UsageChart
            analytics={usageAnalytics}
            range={analyticsRange}
            onRangeChange={setAnalyticsRange}
          />
        )}

        {userStats.length > 0 && <TopContributors users={userStats} />}
      </div>
    </div>
  );
};

export default StatsDashboard;

import React, { useState, useEffect, useCallback } from 'react';
import {
  ChartBarIcon,
  UsersIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  TrophyIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { adminService } from '../../services/admin.service';
import { PlatformStats, UsageAnalytics, UserStats } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';

const StatsDashboard: React.FC = () => {
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
      console.error('Failed to load analytics data:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [analyticsRange]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'sworik_developer':
        return 'bg-purple-100 text-purple-800';
      case 'contributor':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-destructive border border-destructive-border rounded-lg p-6">
        <div className="flex items-center">
          <ChartBarIcon className="h-6 w-6 text-destructive-foreground mr-3" />
          <p className="text-destructive-foreground">{error}</p>
        </div>
        <button
          onClick={loadAllData}
          className="mt-4 bg-destructive text-destructive-foreground px-4 py-2 rounded-lg hover:bg-destructive-hover transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-8 w-8 text-primary" />
          <h2 className="text-2xl font-bold text-foreground">Analytics Dashboard</h2>
        </div>
        <div className="flex items-center space-x-3">
          <CalendarIcon className="h-5 w-5 text-secondary-foreground" />
          <select
            value={analyticsRange}
            onChange={e => setAnalyticsRange(Number(e.target.value))}
            className="px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {/* Platform Overview */}
      {platformStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <div className="flex items-center">
              <UsersIcon className="h-8 w-8 text-primary" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-foreground">{platformStats.total_users}</p>
                <p className="text-sm text-secondary-foreground">Total Users</p>
              </div>
            </div>
            <div className="mt-4 text-xs text-secondary-foreground">
              <div className="flex justify-between">
                <span>Contributors:</span>
                <span>{platformStats.total_contributors}</span>
              </div>
              <div className="flex justify-between">
                <span>Admins:</span>
                <span>{platformStats.total_admins}</span>
              </div>
              <div className="flex justify-between">
                <span>Developers:</span>
                <span>{platformStats.total_sworik_developers}</span>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <div className="flex items-center">
              <MicrophoneIcon className="h-8 w-8 text-success" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-foreground">
                  {platformStats.total_recordings}
                </p>
                <p className="text-sm text-secondary-foreground">Recordings</p>
              </div>
            </div>
            <div className="mt-4 text-xs text-secondary-foreground">
              <div className="flex justify-between">
                <span>Audio Chunks:</span>
                <span>{platformStats.total_chunks}</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Duration:</span>
                <span>
                  {platformStats.avg_recording_duration
                    ? `${platformStats.avg_recording_duration.toFixed(1)}min`
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-info" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-foreground">
                  {platformStats.total_transcriptions}
                </p>
                <p className="text-sm text-secondary-foreground">Transcriptions</p>
              </div>
            </div>
            <div className="mt-4 text-xs text-secondary-foreground">
              <div className="flex justify-between">
                <span>Validated:</span>
                <span>{platformStats.total_validated_transcriptions}</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Quality:</span>
                <span>
                  {platformStats.avg_transcription_quality
                    ? platformStats.avg_transcription_quality.toFixed(2)
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <div className="flex items-center">
              <TrophyIcon className="h-8 w-8 text-warning" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-foreground">
                  {platformStats.total_quality_reviews}
                </p>
                <p className="text-sm text-secondary-foreground">Quality Reviews</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Usage Analytics */}
      {usageAnalytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Activity Chart */}
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">Daily Activity</h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-secondary-foreground mb-2">
                  Recent Recordings
                </h4>
                <div className="space-y-2">
                  {usageAnalytics.daily_recordings.slice(-7).map((day, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="text-sm text-secondary-foreground">
                        {formatDate(day.date)}
                      </span>
                      <div className="flex items-center">
                        <div className="w-24 bg-background rounded-full h-2 mr-2">
                          <div
                            className="bg-success h-2 rounded-full"
                            style={{
                              width: `${Math.min(100, (day.count / Math.max(...usageAnalytics.daily_recordings.map(d => d.count))) * 100)}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-foreground">{day.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-secondary-foreground mb-2">
                  Recent Transcriptions
                </h4>
                <div className="space-y-2">
                  {usageAnalytics.daily_transcriptions.slice(-7).map((day, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="text-sm text-secondary-foreground">
                        {formatDate(day.date)}
                      </span>
                      <div className="flex items-center">
                        <div className="w-24 bg-background rounded-full h-2 mr-2">
                          <div
                            className="bg-info h-2 rounded-full"
                            style={{
                              width: `${Math.min(100, (day.count / Math.max(...usageAnalytics.daily_transcriptions.map(d => d.count))) * 100)}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-foreground">{day.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* User Activity by Role */}
          <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">User Activity by Role</h3>
            <div className="space-y-4">
              {Object.entries(usageAnalytics.user_activity_by_role).map(([role, count]) => (
                <div key={role} className="flex justify-between items-center">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(role)}`}
                  >
                    {role.replace('_', ' ')}
                  </span>
                  <div className="flex items-center">
                    <div className="w-32 bg-background rounded-full h-2 mr-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{
                          width: `${Math.min(100, (count / Math.max(...Object.values(usageAnalytics.user_activity_by_role))) * 100)}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-foreground">{count}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6">
              <h4 className="text-sm font-medium text-secondary-foreground mb-2">
                Popular Script Durations
              </h4>
              <div className="space-y-2">
                {Object.entries(usageAnalytics.popular_script_durations).map(
                  ([duration, count]) => (
                    <div key={duration} className="flex justify-between items-center">
                      <span className="text-sm text-secondary-foreground">
                        {duration.replace('_', ' ')}
                      </span>
                      <div className="flex items-center">
                        <div className="w-24 bg-background rounded-full h-2 mr-2">
                          <div
                            className="bg-warning h-2 rounded-full"
                            style={{
                              width: `${Math.min(100, (count / Math.max(...Object.values(usageAnalytics.popular_script_durations))) * 100)}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-foreground">{count}</span>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Contributors */}
      {usageAnalytics && usageAnalytics.top_contributors.length > 0 && (
        <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground">Top Contributors</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-background">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Contributor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Contributions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                    Role
                  </th>
                </tr>
              </thead>
              <tbody className="bg-card divide-y divide-border">
                {usageAnalytics.top_contributors.map((contributor, index) => {
                  const userStat = userStats.find(u => u.user_id === contributor.user_id);
                  return (
                    <tr key={contributor.user_id} className="hover:bg-background">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {index < 3 && (
                            <TrophyIcon
                              className={`h-5 w-5 mr-2 ${
                                index === 0
                                  ? 'text-warning'
                                  : index === 1
                                    ? 'text-mute'
                                    : 'text-primary'
                              }`}
                            />
                          )}
                          <span className="text-sm font-medium text-foreground">#{index + 1}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-foreground">
                          {contributor.name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-foreground">
                          {contributor.contribution_count}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {userStat && (
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(userStat.role)}`}
                          >
                            {userStat.role.replace('_', ' ')}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quality Trend */}
      {usageAnalytics && usageAnalytics.transcription_quality_trend.length > 0 && (
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            Transcription Quality Trend
          </h3>
          <div className="space-y-2">
            {usageAnalytics.transcription_quality_trend.slice(-10).map((trend, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-sm text-secondary-foreground">{formatDate(trend.date)}</span>
                <div className="flex items-center">
                  <div className="w-32 bg-background rounded-full h-2 mr-2">
                    <div
                      className="bg-success h-2 rounded-full"
                      style={{ width: `${(trend.quality / 5) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {trend.quality.toFixed(2)}/5.0
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsDashboard;

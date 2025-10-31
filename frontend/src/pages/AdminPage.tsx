import React, { useState, useEffect } from 'react';
import { 
  Cog6ToothIcon, 
  UsersIcon, 
  DocumentTextIcon, 
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { PlatformStats, SystemHealth } from '../types/api';
import { 
  UserManagement, 
  ScriptManagement, 
  QualityReview, 
  StatsDashboard 
} from '../components/admin';
import LoadingSpinner from '../components/common/LoadingSpinner';

type TabType = 'overview' | 'users' | 'scripts' | 'quality' | 'stats';

const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [platformStats, setPlatformStats] = useState<PlatformStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOverviewData();
  }, []);

  const loadOverviewData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, healthData] = await Promise.all([
        apiService.getPlatformStats(),
        apiService.getSystemHealth()
      ]);
      setPlatformStats(statsData);
      setSystemHealth(healthData);
    } catch (err) {
      console.error('Failed to load admin overview data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview' as TabType, name: 'Overview', icon: ChartBarIcon },
    { id: 'users' as TabType, name: 'Users', icon: UsersIcon },
    { id: 'scripts' as TabType, name: 'Scripts', icon: DocumentTextIcon },
    { id: 'quality' as TabType, name: 'Quality Review', icon: ExclamationTriangleIcon },
    { id: 'stats' as TabType, name: 'Analytics', icon: ChartBarIcon },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'users':
        return <UserManagement />;
      case 'scripts':
        return <ScriptManagement />;
      case 'quality':
        return <QualityReview />;
      case 'stats':
        return <StatsDashboard />;
      default:
        return renderOverview();
    }
  };

  const renderOverview = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner />
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <XCircleIcon className="h-6 w-6 text-red-600 mr-3" />
            <p className="text-red-800">{error}</p>
          </div>
          <button
            onClick={loadOverviewData}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* System Health */}
        {systemHealth && (
          <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              {systemHealth.database_status === 'healthy' ? (
                <CheckCircleIcon className="h-6 w-6 text-green-600 mr-2" />
              ) : (
                <XCircleIcon className="h-6 w-6 text-red-600 mr-2" />
              )}
              System Health
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{systemHealth.active_users_last_24h}</p>
                <p className="text-sm text-gray-600">Active Users (24h)</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{systemHealth.processing_queue_size}</p>
                <p className="text-sm text-gray-600">Processing Queue</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{systemHealth.failed_recordings_count}</p>
                <p className="text-sm text-gray-600">Failed Recordings</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">
                  {systemHealth.avg_response_time ? `${systemHealth.avg_response_time.toFixed(0)}ms` : 'N/A'}
                </p>
                <p className="text-sm text-gray-600">Avg Response Time</p>
              </div>
            </div>
          </div>
        )}

        {/* Platform Statistics */}
        {platformStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Users</h4>
              <p className="text-3xl font-bold text-blue-600">{platformStats.total_users}</p>
              <div className="mt-2 text-sm text-gray-600">
                <p>Contributors: {platformStats.total_contributors}</p>
                <p>Admins: {platformStats.total_admins}</p>
                <p>Developers: {platformStats.total_sworik_developers}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Recordings</h4>
              <p className="text-3xl font-bold text-green-600">{platformStats.total_recordings}</p>
              <div className="mt-2 text-sm text-gray-600">
                <p>Chunks: {platformStats.total_chunks}</p>
                <p>Avg Duration: {platformStats.avg_recording_duration ? `${platformStats.avg_recording_duration.toFixed(1)}min` : 'N/A'}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Transcriptions</h4>
              <p className="text-3xl font-bold text-purple-600">{platformStats.total_transcriptions}</p>
              <div className="mt-2 text-sm text-gray-600">
                <p>Validated: {platformStats.total_validated_transcriptions}</p>
                <p>Avg Quality: {platformStats.avg_transcription_quality ? platformStats.avg_transcription_quality.toFixed(2) : 'N/A'}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Quality Reviews</h4>
              <p className="text-3xl font-bold text-orange-600">{platformStats.total_quality_reviews}</p>
              <div className="mt-2 text-sm text-gray-600">
                <p>Pending reviews available</p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => setActiveTab('users')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            >
              <UsersIcon className="h-8 w-8 text-blue-600 mb-2" />
              <p className="font-medium text-gray-900">Manage Users</p>
              <p className="text-sm text-gray-600">View and edit user roles</p>
            </button>
            <button
              onClick={() => setActiveTab('scripts')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            >
              <DocumentTextIcon className="h-8 w-8 text-green-600 mb-2" />
              <p className="font-medium text-gray-900">Manage Scripts</p>
              <p className="text-sm text-gray-600">Add and edit Bangla scripts</p>
            </button>
            <button
              onClick={() => setActiveTab('quality')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            >
              <ExclamationTriangleIcon className="h-8 w-8 text-orange-600 mb-2" />
              <p className="font-medium text-gray-900">Quality Review</p>
              <p className="text-sm text-gray-600">Review flagged transcriptions</p>
            </button>
            <button
              onClick={() => setActiveTab('stats')}
              className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-left"
            >
              <ChartBarIcon className="h-8 w-8 text-purple-600 mb-2" />
              <p className="font-medium text-gray-900">View Analytics</p>
              <p className="text-sm text-gray-600">Platform usage statistics</p>
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="text-center mb-8">
        <Cog6ToothIcon className="mx-auto h-16 w-16 text-purple-600 mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">
          Manage users, scripts, and monitor platform activity
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default AdminPage;
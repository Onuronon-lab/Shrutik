import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MicrophoneIcon, DocumentTextIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { CurrentUserStats } from '../types/api';
import LoadingSpinner from '../components/common/LoadingSpinner';

const HomePage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [userStats, setUserStats] = useState<CurrentUserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadUserStats();
    }
  }, [isAuthenticated]);

  const loadUserStats = async () => {
    try {
      setStatsLoading(true);
      const stats = await apiService.getCurrentUserStats();
      setUserStats(stats);
    } catch (error) {
      console.error('Failed to load user stats:', error);
    } finally {
      setStatsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center">
        <div className="max-w-3xl mx-auto">
          <MicrophoneIcon className="mx-auto h-16 w-16 text-indigo-600 mb-8" />
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Voice Collection Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Help us build better AI by contributing your voice and transcription skills
          </p>
          <Link
            to="/login"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg text-lg font-medium transition-colors"
          >
            Get Started
          </Link>
        </div>
      </div>
    );
  }

  const features = [
    {
      name: 'Record Voice',
      description: 'Read Bangla scripts and contribute voice recordings',
      icon: MicrophoneIcon,
      href: '/record',
      color: 'bg-blue-500',
    },
    {
      name: 'Transcribe Audio',
      description: 'Listen to audio clips and provide accurate transcriptions',
      icon: DocumentTextIcon,
      href: '/transcribe',
      color: 'bg-green-500',
    },
  ];

  if (user?.role === 'admin' || user?.role === 'sworik_developer') {
    features.push({
      name: 'Admin Dashboard',
      description: 'Manage users, scripts, and monitor platform activity',
      icon: ChartBarIcon,
      href: '/admin',
      color: 'bg-purple-500',
    });
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-xl text-gray-600">
          Choose how you'd like to contribute today
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.name}
              to={feature.href}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200"
            >
              <div className={`w-12 h-12 ${feature.color} rounded-lg flex items-center justify-center mb-4`}>
                <Icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {feature.name}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </Link>
          );
        })}
      </div>

      <div className="mt-12 bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Contribution Stats</h2>
        {statsLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600 mb-2">
                {userStats?.recordings_count || 0}
              </div>
              <div className="text-gray-600">Voice Recordings</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {userStats?.transcriptions_count || 0}
              </div>
              <div className="text-gray-600">Transcriptions</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {userStats?.avg_transcription_quality ? userStats.avg_transcription_quality.toFixed(1) : 'N/A'}
              </div>
              <div className="text-gray-600">Quality Score</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
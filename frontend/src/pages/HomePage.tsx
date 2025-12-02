import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  MicrophoneIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { CurrentUserStats } from '../types/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTranslation } from 'react-i18next';

const HomePage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [userStats, setUserStats] = useState<CurrentUserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const { t } = useTranslation();

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
          <MicrophoneIcon className="mx-auto h-16 w-16 text-primary mb-8" />
          <h1 className="text-4xl font-bold text-foreground mb-4">Shrutik</h1>
          <p className="text-xl text-secondary-foreground mb-8">
            Help us build better AI by contributing your voice and transcription skills
          </p>
          <Link
            to="/login"
            className="bg-primary hover:bg-primary-hover text-primary-foreground px-8 py-3 rounded-lg text-lg font-medium transition-colors"
          >
            Get Started
          </Link>
        </div>
      </div>
    );
  }

  const features = [
    {
      name: t('record-voice'),
      description: t('record-voice-description'),
      icon: MicrophoneIcon,
      href: '/record',
      bgcolor: 'bg-primary',
      color: 'text-primary-foreground',
    },
    {
      name: t('transcribe-audio'),
      description: t('transcribe-audio-description'),
      icon: DocumentTextIcon,
      href: '/transcribe',
      bgcolor: 'bg-success',
      color: 'text-success-foreground',
    },
  ];

  if (user?.role === 'sworik_developer') {
    features.push({
      name: 'Export Data',
      description: 'Download validated datasets for AI training',
      icon: ArrowDownTrayIcon,
      href: '/export',
      bgcolor: 'bg-info',
      color: 'text-info-foreground',
    });
  }

  if (user?.role === 'admin') {
    features.push({
      name: t('admin-dashboard'),
      description: t('admin-dashboard-description'),
      icon: ChartBarIcon,
      href: '/admin',
      bgcolor: 'bg-info',
      color: 'text-info-foreground',
    });
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-foreground mb-4">
          {t('welcome')}, {user?.name}!
        </h1>
        <p className="text-xl text-secondary-foreground">{t('choose-contribution')}</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map(feature => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.name}
              to={feature.href}
              className="bg-card rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-border"
            >
              <div
                className={`w-12 h-12 ${feature.bgcolor} rounded-lg flex items-center justify-center mb-4`}
              >
                <Icon className={`h-6 w-6 ${feature.color}`} />
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-2">{feature.name}</h3>
              <p className="text-secondary-foreground">{feature.description}</p>
            </Link>
          );
        })}
      </div>

      <div className="mt-12 bg-card rounded-lg shadow-md p-6 border border-border">
        <h2 className="text-2xl font-bold text-foreground mb-4">{t('contribution-stat-title')}</h2>
        {statsLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary mb-2">
                {userStats?.recordings_count || 0}
              </div>
              <div className="text-secondary-foreground">{t('contribution-voice-recording')}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-success mb-2">
                {userStats?.transcriptions_count || 0}
              </div>
              <div className="text-secondary-foreground">{t('contribution-transcription')}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-info mb-2">
                {userStats?.avg_transcription_quality
                  ? userStats.avg_transcription_quality.toFixed(1)
                  : 'N/A'}
              </div>
              <div className="text-secondary-foreground">{t('contribution-quality-score')}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;

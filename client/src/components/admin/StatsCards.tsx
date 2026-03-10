import React from 'react';
import {
  UsersIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  TrophyIcon,
} from '@heroicons/react/24/outline';
import { PlatformStats } from '../../types/api';

interface StatsCardsProps {
  stats: PlatformStats;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  const cards = [
    {
      title: 'Total Users',
      value: stats.total_users,
      icon: UsersIcon,
      color: 'bg-blue-500',
    },
    {
      title: 'Total Recordings',
      value: stats.total_recordings,
      icon: MicrophoneIcon,
      color: 'bg-green-500',
    },
    {
      title: 'Total Transcriptions',
      value: stats.total_transcriptions,
      icon: DocumentTextIcon,
      color: 'bg-purple-500',
    },
    {
      title: 'Quality Reviews',
      value: stats.total_quality_reviews,
      icon: TrophyIcon,
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-2 rounded-lg ${card.color}`}>
                  <card.icon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    {card.title}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-white">
                    {card.value.toLocaleString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;

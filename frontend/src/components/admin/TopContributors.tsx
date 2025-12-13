import React from 'react';
import { TrophyIcon } from '@heroicons/react/24/outline';
import { UserStats } from '../../types/api';

interface TopContributorsProps {
  users: UserStats[];
}

const TopContributors: React.FC<TopContributorsProps> = ({ users }) => {
  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300';
      case 'sworik_developer':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300';
      case 'contributor':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center mb-4">
        <TrophyIcon className="h-5 w-5 text-yellow-500 dark:text-yellow-400 mr-2" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Top Contributors</h3>
      </div>

      <div className="space-y-3">
        {users.slice(0, 10).map((user, index) => (
          <div
            key={user.user_id}
            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-100 dark:border-gray-600"
          >
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-500 dark:bg-indigo-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  #{index + 1}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{user.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user.recordings_count} recordings
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {user.transcriptions_count} transcriptions
                </p>
              </div>

              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}
              >
                {user.role === 'sworik_developer' ? 'sworik developer' : user.role}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopContributors;

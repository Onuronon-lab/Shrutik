import React from 'react';
import { UsageAnalytics } from '../../types/api';

interface UsageChartProps {
  analytics: UsageAnalytics;
  range: number;
  onRangeChange: (range: number) => void;
}

const UsageChart: React.FC<UsageChartProps> = ({ analytics, range, onRangeChange }) => {
  // Handle empty or undefined data
  const recordingsData = analytics?.daily_recordings || [];
  const transcriptionsData = analytics?.daily_transcriptions || [];

  const maxRecordings = Math.max(...recordingsData.map(d => d.count), 1);
  const maxTranscriptions = Math.max(...transcriptionsData.map(d => d.count), 1);

  const hasRecordingData = recordingsData.some(d => d.count > 0);
  const hasTranscriptionData = transcriptionsData.some(d => d.count > 0);

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Usage Analytics</h3>
        <select
          value={range}
          onChange={e => onRangeChange(Number(e.target.value))}
          className="block w-32 px-3 py-2 text-base border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <div className="space-y-6">
        {/* Recordings Chart */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Daily Recordings
          </h4>
          <div className="flex items-end space-x-1 h-32 bg-gray-50 dark:bg-gray-700 rounded p-2">
            {!hasRecordingData ? (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                <div className="text-center">
                  <p>No recording data for the last {range} days</p>
                  <p className="text-xs mt-1">Start recording to see analytics</p>
                </div>
              </div>
            ) : (
              recordingsData.slice(-Math.min(range, 30)).map((day, index) => (
                <div key={index} className="flex-1 flex flex-col items-center min-w-0">
                  <div
                    className="w-full bg-blue-500 dark:bg-blue-400 rounded-t transition-all duration-200 hover:bg-blue-600 dark:hover:bg-blue-300"
                    style={{
                      height: `${Math.max((day.count / maxRecordings) * 100, day.count > 0 ? 8 : 0)}%`,
                      minHeight: day.count > 0 ? '4px' : '0px',
                    }}
                    title={`${day.count} recordings on ${new Date(day.date).toLocaleDateString()}`}
                  />
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 transform -rotate-45 origin-left truncate">
                    {new Date(day.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Transcriptions Chart */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Daily Transcriptions
          </h4>
          <div className="flex items-end space-x-1 h-32 bg-gray-50 dark:bg-gray-700 rounded p-2">
            {!hasTranscriptionData ? (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                <div className="text-center">
                  <p>No transcription data for the last {range} days</p>
                  <p className="text-xs mt-1">Complete transcriptions to see analytics</p>
                </div>
              </div>
            ) : (
              transcriptionsData.slice(-Math.min(range, 30)).map((day, index) => (
                <div key={index} className="flex-1 flex flex-col items-center min-w-0">
                  <div
                    className="w-full bg-green-500 dark:bg-green-400 rounded-t transition-all duration-200 hover:bg-green-600 dark:hover:bg-green-300"
                    style={{
                      height: `${Math.max((day.count / maxTranscriptions) * 100, day.count > 0 ? 8 : 0)}%`,
                      minHeight: day.count > 0 ? '4px' : '0px',
                    }}
                    title={`${day.count} transcriptions on ${new Date(day.date).toLocaleDateString()}`}
                  />
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 transform -rotate-45 origin-left truncate">
                    {new Date(day.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsageChart;

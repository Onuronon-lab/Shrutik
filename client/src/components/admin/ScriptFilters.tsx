import React from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui';

interface ScriptFiltersProps {
  searchTerm: string;
  durationFilter: string;
  onSearchChange: (value: string) => void;
  onDurationFilterChange: (value: string) => void;
  onCreateNew: () => void;
}

const ScriptFilters: React.FC<ScriptFiltersProps> = ({
  searchTerm,
  durationFilter,
  onSearchChange,
  onDurationFilterChange,
  onCreateNew,
}) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 dark:text-gray-500" />
          </div>
          <input
            type="text"
            placeholder="Search scripts..."
            value={searchTerm}
            onChange={e => onSearchChange(e.target.value)}
            className="search-input block w-full pl-9 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 dark:focus:placeholder-gray-300 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          />
        </div>

        <select
          value={durationFilter}
          onChange={e => onDurationFilterChange(e.target.value)}
          className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value="">All Durations</option>
          <option value="2_minutes">2 Minutes</option>
          <option value="5_minutes">5 Minutes</option>
          <option value="10_minutes">10 Minutes</option>
        </select>
      </div>

      <Button onClick={onCreateNew}>+ Add Script</Button>
    </div>
  );
};

export default ScriptFilters;

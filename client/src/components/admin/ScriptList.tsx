import React from 'react';
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import { Script } from '../../types/api';

interface ScriptListProps {
  scripts: Script[];
  onEdit: (script: Script) => void;
  onDelete: (scriptId: number) => void;
  getDurationLabel: (category: string) => string;
  getDurationColor: (category: string) => string;
  formatDate: (dateString: string) => string;
}

const ScriptList: React.FC<ScriptListProps> = ({
  scripts,
  onEdit,
  onDelete,
  getDurationLabel,
  getDurationColor,
  formatDate,
}) => {
  const handleDelete = (scriptId: number) => {
    if (
      window.confirm('Are you sure you want to delete this script? This action cannot be undone.')
    ) {
      onDelete(scriptId);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md border border-gray-200 dark:border-gray-700">
      <ul className="divide-y divide-gray-200 dark:divide-gray-700">
        {scripts.map(script => (
          <li key={script.id}>
            <div className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDurationColor(
                        script.duration_category
                      )}`}
                    >
                      {getDurationLabel(script.duration_category)}
                    </span>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Created: {formatDate(script.created_at)}
                    </p>
                  </div>
                  <p className="mt-2 text-sm text-gray-900 dark:text-white line-clamp-3">
                    {script.text}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onEdit(script)}
                    className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(script.id)}
                    className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ScriptList;

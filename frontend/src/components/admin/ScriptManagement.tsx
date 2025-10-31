import React, { useState, useEffect, useCallback } from 'react';
import { 
  DocumentTextIcon, 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import { Script, ScriptListResponse, ScriptValidation } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';

const ScriptManagement: React.FC = () => {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [durationFilter, setDurationFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingScript, setEditingScript] = useState<Script | null>(null);
  const [formData, setFormData] = useState({
    text: '',
    duration_category: '2_minutes',
    language_id: 1,
    meta_data: {}
  });
  const [validation, setValidation] = useState<ScriptValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0
  });

  const loadScripts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const skip = (pagination.page - 1) * pagination.per_page;
      const data: ScriptListResponse = await apiService.getScripts(
        skip, 
        pagination.per_page, 
        durationFilter || undefined
      );
      setScripts(data.scripts);
      setPagination({
        page: data.page,
        per_page: data.per_page,
        total: data.total,
        total_pages: data.total_pages
      });
    } catch (err) {
      console.error('Failed to load scripts:', err);
      setError('Failed to load scripts. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [durationFilter, pagination.page, pagination.per_page]);

  useEffect(() => {
    loadScripts();
  }, [loadScripts]);

  const validateScript = async () => {
    if (!formData.text.trim()) return;

    try {
      setValidating(true);
      const result = await apiService.validateScript(formData.text, formData.duration_category);
      setValidation(result);
    } catch (err) {
      console.error('Failed to validate script:', err);
      setError('Failed to validate script. Please try again.');
    } finally {
      setValidating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      setError(null);

      if (editingScript) {
        await apiService.updateScript(editingScript.id, formData);
      } else {
        await apiService.createScript(formData);
      }

      // Reset form and close modal
      setFormData({
        text: '',
        duration_category: '2_minutes',
        language_id: 1,
        meta_data: {}
      });
      setValidation(null);
      setShowCreateModal(false);
      setEditingScript(null);
      
      // Reload scripts
      await loadScripts();
    } catch (err) {
      console.error('Failed to save script:', err);
      setError('Failed to save script. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (scriptId: number) => {
    if (!window.confirm('Are you sure you want to delete this script? This action cannot be undone.')) {
      return;
    }

    try {
      await apiService.deleteScript(scriptId);
      await loadScripts();
    } catch (err) {
      console.error('Failed to delete script:', err);
      setError('Failed to delete script. Please try again.');
    }
  };

  const openEditModal = (script: Script) => {
    setEditingScript(script);
    setFormData({
      text: script.text,
      duration_category: script.duration_category,
      language_id: script.language_id,
      meta_data: script.meta_data || {}
    });
    setValidation(null);
    setShowCreateModal(true);
  };

  const closeModal = () => {
    setShowCreateModal(false);
    setEditingScript(null);
    setFormData({
      text: '',
      duration_category: '2_minutes',
      language_id: 1,
      meta_data: {}
    });
    setValidation(null);
    setError(null);
  };

  const filteredScripts = scripts.filter(script => 
    script.text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getDurationLabel = (category: string) => {
    switch (category) {
      case '2_minutes':
        return '2 Minutes';
      case '5_minutes':
        return '5 Minutes';
      case '10_minutes':
        return '10 Minutes';
      default:
        return category;
    }
  };

  const getDurationColor = (category: string) => {
    switch (category) {
      case '2_minutes':
        return 'bg-green-100 text-green-800';
      case '5_minutes':
        return 'bg-yellow-100 text-yellow-800';
      case '10_minutes':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading && scripts.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <DocumentTextIcon className="h-8 w-8 text-green-600" />
          <h2 className="text-2xl font-bold text-gray-900">Script Management</h2>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Add Script</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search scripts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
          <select
            value={durationFilter}
            onChange={(e) => setDurationFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          >
            <option value="">All Durations</option>
            <option value="2_minutes">2 Minutes</option>
            <option value="5_minutes">5 Minutes</option>
            <option value="10_minutes">10 Minutes</option>
          </select>
        </div>
      </div>

      {/* Scripts Table */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Script Text
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredScripts.map((script) => (
                <tr key={script.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      <p className="line-clamp-3">{script.text}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDurationColor(script.duration_category)}`}>
                      {getDurationLabel(script.duration_category)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(script.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => openEditModal(script)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(script.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredScripts.length === 0 && (
          <div className="text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No scripts found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || durationFilter ? 'Try adjusting your filters.' : 'Get started by adding a new script.'}
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((pagination.page - 1) * pagination.per_page) + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} scripts
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
              disabled={pagination.page === 1}
              className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={pagination.page === pagination.total_pages}
              className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Script Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingScript ? 'Edit Script' : 'Add New Script'}
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Duration Category
                  </label>
                  <select
                    value={formData.duration_category}
                    onChange={(e) => setFormData({ ...formData, duration_category: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="2_minutes">2 Minutes</option>
                    <option value="5_minutes">5 Minutes</option>
                    <option value="10_minutes">10 Minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Script Text (Bangla)
                  </label>
                  <textarea
                    value={formData.text}
                    onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                    rows={8}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Enter the Bangla script text here..."
                    required
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={validateScript}
                    disabled={!formData.text.trim() || validating}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {validating && <LoadingSpinner size="sm" className="mr-2" />}
                    <ClockIcon className="h-4 w-4 mr-2" />
                    Validate Script
                  </button>
                </div>

                {validation && (
                  <div className={`p-4 rounded-lg ${validation.is_valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    <div className="flex items-center mb-2">
                      {validation.is_valid ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
                      ) : (
                        <XCircleIcon className="h-5 w-5 text-red-600 mr-2" />
                      )}
                      <span className={`font-medium ${validation.is_valid ? 'text-green-800' : 'text-red-800'}`}>
                        {validation.is_valid ? 'Script is valid' : 'Script has issues'}
                      </span>
                    </div>
                    
                    <div className="text-sm space-y-1">
                      <p>Word count: {validation.word_count}</p>
                      <p>Character count: {validation.character_count}</p>
                      {validation.estimated_duration && (
                        <p>Estimated duration: {validation.estimated_duration.toFixed(1)} minutes</p>
                      )}
                    </div>

                    {validation.errors.length > 0 && (
                      <div className="mt-2">
                        <p className="text-red-800 font-medium">Errors:</p>
                        <ul className="list-disc list-inside text-red-700 text-sm">
                          {validation.errors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {validation.warnings.length > 0 && (
                      <div className="mt-2">
                        <p className="text-yellow-800 font-medium">Warnings:</p>
                        <ul className="list-disc list-inside text-yellow-700 text-sm">
                          {validation.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !formData.text.trim()}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {submitting && <LoadingSpinner size="sm" className="mr-2" />}
                    {editingScript ? 'Update Script' : 'Create Script'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScriptManagement;
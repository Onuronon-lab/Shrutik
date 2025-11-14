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
          <DocumentTextIcon className="h-8 w-8 text-success" />
          <h2 className="text-2xl font-bold text-foreground">Script Management</h2>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-success text-success-foreground px-4 py-2 rounded-lg hover:bg-success-hover transition-colors flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Add Script</span>
        </button>
      </div>

      {error && (
        <div className="bg-destructive border border-destructive-border rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="h-5 w-5 text-destructive-foreground mr-2" />
            <p className="text-destructive-foreground">{error}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-card rounded-lg shadow-md p-6 border border-border">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-accent" />
            <input
              type="text"
              placeholder="Search scripts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>
          <select
            value={durationFilter}
            onChange={(e) => setDurationFilter(e.target.value)}
            className="px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
          >
            <option value="">All Durations</option>
            <option value="2_minutes">2 Minutes</option>
            <option value="5_minutes">5 Minutes</option>
            <option value="10_minutes">10 Minutes</option>
          </select>
        </div>
      </div>

      {/* Scripts Table */}
      <div className="bg-card rounded-lg shadow-md border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-background">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Script Text
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filteredScripts.map((script) => (
                <tr key={script.id} className="hover:bg-background">
                  <td className="px-6 py-4">
                    <div className="text-sm text-foreground">
                      <p className="line-clamp-3">{script.text}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDurationColor(script.duration_category)}`}>
                      {getDurationLabel(script.duration_category)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-foreground">
                    {formatDate(script.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => openEditModal(script)}
                        className="text-primary hover:text-primary-hover"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(script.id)}
                        className="text-destructive hover:text-destructive-hover"
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
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-accent" />
            <h3 className="mt-2 text-sm font-medium text-foreground">No scripts found</h3>
            <p className="mt-1 text-sm text-secondary-foreground">
              {searchTerm || durationFilter ? 'Try adjusting your filters.' : 'Get started by adding a new script.'}
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-secondary-foreground">
            Showing {((pagination.page - 1) * pagination.per_page) + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} scripts
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
              disabled={pagination.page === 1}
              className="px-3 py-2 border border-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-background"
            >
              Previous
            </button>
            <button
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={pagination.page === pagination.total_pages}
              className="px-3 py-2 border border-border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-background"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Script Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-card">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-foreground mb-4">
                {editingScript ? 'Edit Script' : 'Add New Script'}
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-2">
                    Duration Category
                  </label>
                  <select
                    value={formData.duration_category}
                    onChange={(e) => setFormData({ ...formData, duration_category: e.target.value as any })}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                  >
                    <option value="2_minutes">2 Minutes</option>
                    <option value="5_minutes">5 Minutes</option>
                    <option value="10_minutes">10 Minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-foreground mb-2">
                    Script Text (Bangla)
                  </label>
                  <textarea
                    value={formData.text}
                    onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                    rows={8}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                    placeholder="Enter the Bangla script text here..."
                    required
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={validateScript}
                    disabled={!formData.text.trim() || validating}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {validating && <LoadingSpinner size="sm" className="mr-2" />}
                    <ClockIcon className="h-4 w-4 mr-2" />
                    Validate Script
                  </button>
                </div>

                {validation && (
                  <div className={`p-4 rounded-lg ${validation.is_valid ? 'bg-success border border-success-border' : 'bg-destructive border border-destructive-border'}`}>
                    <div className="flex items-center mb-2">
                      {validation.is_valid ? (
                        <CheckCircleIcon className="h-5 w-5 text-success-foreground mr-2" />
                      ) : (
                        <XCircleIcon className="h-5 w-5 text-destructive-foreground mr-2" />
                      )}
                      <span className={`font-medium ${validation.is_valid ? 'text-success-foreground' : 'text-destructive-foreground'}`}>
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
                        <p className="text-destructive-foreground font-medium">Errors:</p>
                        <ul className="list-disc list-inside text-destructive-foreground text-sm">
                          {validation.errors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {validation.warnings.length > 0 && (
                      <div className="mt-2">
                        <p className="text-warning-foreground font-medium">Warnings:</p>
                        <ul className="list-disc list-inside text-warning-foreground text-sm">
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
                    className="px-4 py-2 text-secondary-foreground border border-border rounded-lg hover:bg-background"
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !formData.text.trim()}
                    className="px-4 py-2 bg-success text-success-foreground rounded-lg hover:bg-success-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
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
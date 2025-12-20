import React, { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { scriptService } from '../../services/script.service';
import { Script, ScriptListResponse, ScriptValidation } from '../../types/api';
import LoadingSpinner from '../common/LoadingSpinner';
import { scriptSchema, type ScriptFormData } from '../../schemas/script.schema';
import { Modal } from '../ui';
import { useModal } from '../../hooks/useModal';
import { useErrorHandler } from '../../hooks/useErrorHandler';
import ScriptFilters from './ScriptFilters';
import ScriptList from './ScriptList';
import ScriptForm from './ScriptForm';

const ScriptManagement: React.FC = () => {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [durationFilter, setDurationFilter] = useState<string>('');
  const [editingScript, setEditingScript] = useState<Script | null>(null);
  const [validation, setValidation] = useState<ScriptValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const createModal = useModal();
  const { error, setError } = useErrorHandler();

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<ScriptFormData>({
    resolver: zodResolver(scriptSchema) as any,
    defaultValues: {
      text: '',
      duration_category: '2_minutes',
      language_id: 1,
      meta_data: {},
    },
  });

  const loadScripts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data: ScriptListResponse = await scriptService.getScripts(
        0,
        50,
        durationFilter || undefined
      );
      setScripts(data.scripts);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load scripts');
    } finally {
      setLoading(false);
    }
  }, [searchTerm, durationFilter, setError]);

  useEffect(() => {
    loadScripts();
  }, [loadScripts]);

  const validateScript = async () => {
    const formText = watch('text');
    const formDurationCategory = watch('duration_category');
    if (!formText.trim()) return;

    try {
      setValidating(true);
      const result = await scriptService.validateScript(formText, formDurationCategory);
      setValidation(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate script');
    } finally {
      setValidating(false);
    }
  };

  const onSubmit = async (data: ScriptFormData) => {
    try {
      setSubmitting(true);
      setError(null);

      if (editingScript) {
        await scriptService.updateScript(editingScript.id, data);
      } else {
        await scriptService.createScript(data);
      }

      await loadScripts();
      closeModal();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save script');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (scriptId: number) => {
    try {
      await scriptService.deleteScript(scriptId);
      await loadScripts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete script');
    }
  };

  const openEditModal = (script: Script) => {
    setEditingScript(script);
    reset({
      text: script.text,
      duration_category: script.duration_category,
      language_id: script.language_id,
      meta_data: script.meta_data,
    });
    createModal.open();
  };

  const closeModal = () => {
    createModal.close();
    setEditingScript(null);
    reset();
    setValidation(null);
  };

  const filteredScripts = scripts.filter(script =>
    script.text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getDurationLabel = (category: string) => {
    const labels = {
      '2_minutes': '2 Minutes',
      '5_minutes': '5 Minutes',
      '10_minutes': '10 Minutes',
    };
    return labels[category as keyof typeof labels] || category;
  };

  const getDurationColor = (category: string) => {
    const colors = {
      '2_minutes': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      '5_minutes': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      '10_minutes': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    };
    return (
      colors[category as keyof typeof colors] ||
      'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
    );
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
      <div className="flex items-center space-x-3">
        <DocumentTextIcon className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Script Management</h2>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">
            {typeof error === 'string' ? error : error.error}
          </p>
        </div>
      )}

      <ScriptFilters
        searchTerm={searchTerm}
        durationFilter={durationFilter}
        onSearchChange={setSearchTerm}
        onDurationFilterChange={setDurationFilter}
        onCreateNew={createModal.open}
      />

      <ScriptList
        scripts={filteredScripts}
        onEdit={openEditModal}
        onDelete={handleDelete}
        getDurationLabel={getDurationLabel}
        getDurationColor={getDurationColor}
        formatDate={formatDate}
      />

      <Modal
        isOpen={createModal.isOpen}
        onClose={closeModal}
        title={editingScript ? 'Edit Script' : 'Create New Script'}
      >
        <ScriptForm
          register={register}
          errors={errors}
          watch={watch}
          validation={validation}
          validating={validating}
          submitting={submitting}
          onValidate={validateScript}
          onSubmit={handleSubmit(onSubmit)}
        />
      </Modal>
    </div>
  );
};

export default ScriptManagement;

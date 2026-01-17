import React, { useEffect, useState } from 'react';
import { UseFormRegister, FieldErrors, UseFormWatch } from 'react-hook-form';
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';
import { ScriptValidation } from '../../types/api';
import { ScriptFormData } from '../../schemas/script.schema';
import { FormTextarea, FormSelect, Button } from '../ui';
import { adminService } from '../../services/admin.service';

interface Language {
  id: number;
  name: string;
  code: string;
}

interface ScriptFormProps {
  register: UseFormRegister<ScriptFormData>;
  errors: FieldErrors<ScriptFormData>;
  watch: UseFormWatch<ScriptFormData>;
  validation: ScriptValidation | null;
  validating: boolean;
  submitting: boolean;
  onValidate: () => void;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
}

const ScriptForm: React.FC<ScriptFormProps> = ({
  register,
  errors,
  watch,
  validation,
  validating,
  submitting,
  onValidate,
  onSubmit,
}) => {
  const formText = watch('text');
  const [languages, setLanguages] = useState<Language[]>([]);

  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        const data = await adminService.getLanguages();
        setLanguages(data);
      } catch (error) {
        console.error('Failed to fetch languages:', error);
        // Fallback to default languages if API fails
        setLanguages([
          { id: 1, name: 'English', code: 'en' },
          { id: 2, name: 'Bengali', code: 'bn' },
        ]);
      }
    };

    fetchLanguages();
  }, []);

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div>
        <FormTextarea
          register={register}
          errors={errors}
          name="text"
          label="Script Text"
          rows={8}
          placeholder="Enter the script text here..."
        />
      </div>

      <div>
        <FormSelect
          register={register}
          errors={errors}
          name="duration_category"
          label="Duration Category"
        >
          <option value="2_minutes">2 Minutes</option>
          <option value="5_minutes">5 Minutes</option>
          <option value="10_minutes">10 Minutes</option>
        </FormSelect>
      </div>

      <div>
        <FormSelect register={register} errors={errors} name="language_id" label="Language">
          {languages.map(language => (
            <option key={language.id} value={language.id}>
              {language.name}
            </option>
          ))}
        </FormSelect>
      </div>

      {/* Validation Section */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Script Validation</h3>
          <Button
            type="button"
            variant="secondary"
            onClick={onValidate}
            disabled={!formText.trim() || validating}
          >
            {validating ? (
              <>
                <ClockIcon className="w-4 h-4 mr-2 animate-spin" />
                Validating...
              </>
            ) : (
              'Validate Script'
            )}
          </Button>
        </div>

        {validation && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              {validation.is_valid ? (
                <CheckCircleIcon className="w-5 h-5 text-green-500 dark:text-green-400" />
              ) : (
                <XCircleIcon className="w-5 h-5 text-red-500 dark:text-red-400" />
              )}
              <span
                className={`font-medium ${
                  validation.is_valid
                    ? 'text-green-700 dark:text-green-300'
                    : 'text-red-700 dark:text-red-300'
                }`}
              >
                {validation.is_valid ? 'Script is valid' : 'Script has issues'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm text-gray-900 dark:text-white">
              <div>
                <span className="font-medium">Word Count:</span> {validation.word_count}
              </div>
              <div>
                <span className="font-medium">Character Count:</span> {validation.character_count}
              </div>
              {validation.estimated_duration && (
                <div>
                  <span className="font-medium">Estimated Duration:</span>{' '}
                  {Math.round(validation.estimated_duration)} seconds
                </div>
              )}
            </div>

            {validation.errors.length > 0 && (
              <div>
                <h4 className="font-medium text-red-700 dark:text-red-300 mb-2">Errors:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-red-600 dark:text-red-400">
                  {validation.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {validation.warnings.length > 0 && (
              <div>
                <h4 className="font-medium text-yellow-700 dark:text-yellow-300 mb-2">Warnings:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-yellow-600 dark:text-yellow-400">
                  {validation.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : 'Save Script'}
        </Button>
      </div>
    </form>
  );
};

export default ScriptForm;

import React from 'react';

interface FormFieldProps {
  label: string;
  id: string;
  type?: string;
  value: string;
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
  className?: string;
  as?: 'input' | 'textarea' | 'select';
  children?: React.ReactNode;
  rows?: number;
}

const FormField: React.FC<FormFieldProps> = ({
  label,
  id,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  error,
  className = '',
  as = 'input',
  children,
  rows = 3,
}) => {
  const baseClasses = `
    block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
    focus:outline-none focus:ring-indigo-500 focus:border-indigo-500
    ${error ? 'border-red-300' : ''}
  `;

  const renderField = () => {
    switch (as) {
      case 'textarea':
        return (
          <textarea
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            required={required}
            rows={rows}
            className={baseClasses}
          />
        );
      case 'select':
        return (
          <select
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            required={required}
            className={baseClasses}
          >
            {children}
          </select>
        );
      default:
        return (
          <input
            type={type}
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            required={required}
            className={baseClasses}
          />
        );
    }
  };

  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderField()}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};

export default FormField;

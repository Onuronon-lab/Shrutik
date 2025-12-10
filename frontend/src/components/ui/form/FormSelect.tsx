import React from 'react';
import { UseFormRegister, FieldErrors, FieldValues, Path } from 'react-hook-form';
import { cn } from '../../../utils/cn';

interface FormSelectProps<T extends FieldValues> extends Omit<
  React.SelectHTMLAttributes<HTMLSelectElement>,
  'className'
> {
  register: UseFormRegister<T>;
  errors: FieldErrors<T>;
  name: Path<T>;
  label?: string;
  className?: string;
  showLabel?: boolean;
  children: React.ReactNode;
}

export function FormSelect<T extends FieldValues>({
  register,
  errors,
  name,
  label,
  className,
  showLabel = true,
  children,
  ...props
}: FormSelectProps<T>) {
  const error = errors[name];
  const hasError = !!error;
  const { className: selectClassName, ...selectProps } = props as any;

  return (
    <div className={className}>
      {showLabel && label && (
        <label
          htmlFor={name as string}
          className="block text-sm font-medium text-secondary-foreground mb-2"
        >
          {label}
        </label>
      )}
      <select
        id={name as string}
        {...register(name)}
        {...selectProps}
        className={cn(
          'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2',
          hasError
            ? 'border-destructive focus:ring-destructive focus:border-destructive'
            : 'border-border focus:ring-ring focus:border-transparent',
          selectClassName
        )}
      >
        {children}
      </select>
      {error && <div className="text-destructive text-sm mt-1">{error.message as string}</div>}
    </div>
  );
}

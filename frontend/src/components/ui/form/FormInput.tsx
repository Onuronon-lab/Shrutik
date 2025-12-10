import React from 'react';
import { UseFormRegister, FieldErrors, FieldValues, Path } from 'react-hook-form';
import { cn } from '../../../utils/cn';

interface FormInputProps<T extends FieldValues> extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'className'
> {
  register: UseFormRegister<T>;
  errors: FieldErrors<T>;
  name: Path<T>;
  label?: string;
  className?: string;
  showLabel?: boolean;
}

export function FormInput<T extends FieldValues>({
  register,
  errors,
  name,
  label,
  className,
  showLabel = true,
  ...props
}: FormInputProps<T>) {
  const error = errors[name];
  const hasError = !!error;

  // Extract className from props if it exists
  const { className: inputClassName, ...inputProps } = props as any;

  return (
    <div className={className}>
      {showLabel && label && (
        <label htmlFor={name as string} className="sr-only">
          {label}
        </label>
      )}
      <input
        id={name as string}
        {...register(name)}
        {...inputProps}
        className={cn(
          'appearance-none rounded-none relative block w-full px-3 py-2 border',
          'placeholder-nutral text-nutral-foreground focus:outline-none focus:ring-2 sm:text-sm',
          hasError
            ? 'border-destructive focus:ring-destructive focus:border-destructive'
            : 'border-border focus:ring-primary focus:border-primary',
          inputClassName
        )}
      />
      {error && <div className="text-destructive text-sm mt-1">{error.message as string}</div>}
    </div>
  );
}

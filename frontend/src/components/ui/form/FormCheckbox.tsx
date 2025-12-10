import React from 'react';
import { UseFormRegister, FieldErrors, FieldValues, Path } from 'react-hook-form';
import { cn } from '../../../utils/cn';

interface FormCheckboxProps<T extends FieldValues> extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'className'
> {
  register: UseFormRegister<T>;
  errors: FieldErrors<T>;
  name: Path<T>;
  label?: string;
  className?: string;
}

export function FormCheckbox<T extends FieldValues>({
  register,
  errors,
  name,
  label,
  className,
  ...props
}: FormCheckboxProps<T>) {
  const error = errors[name];
  const hasError = !!error;
  const { className: inputClassName, ...inputProps } = props as any;

  return (
    <div className={className}>
      <div className="flex items-center">
        <input
          type="checkbox"
          id={name as string}
          {...register(name)}
          {...inputProps}
          className={cn(
            'h-4 w-4 text-primary focus:ring-primary border-border rounded',
            hasError && 'border-destructive',
            inputClassName
          )}
        />
        {label && (
          <label htmlFor={name as string} className="ml-2 block text-sm text-foreground">
            {label}
          </label>
        )}
      </div>
      {error && <div className="text-destructive text-sm mt-1">{error.message as string}</div>}
    </div>
  );
}

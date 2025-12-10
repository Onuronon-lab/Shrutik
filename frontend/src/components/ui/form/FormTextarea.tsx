import React from 'react';
import { UseFormRegister, FieldErrors, FieldValues, Path } from 'react-hook-form';
import { cn } from '../../../utils/cn';

interface FormTextareaProps<T extends FieldValues> extends Omit<
  React.TextareaHTMLAttributes<HTMLTextAreaElement>,
  'className'
> {
  register: UseFormRegister<T>;
  errors: FieldErrors<T>;
  name: Path<T>;
  label?: string;
  className?: string;
  showLabel?: boolean;
}

export const FormTextarea = React.forwardRef<HTMLTextAreaElement, FormTextareaProps<any>>(
  (props: FormTextareaProps<any>, ref: React.ForwardedRef<HTMLTextAreaElement>) => {
    const { register, errors, name, label, className, showLabel = true, ...restProps } = props;
    const error = errors[name];
    const hasError = !!error;
    const { ref: registerRef, ...registerProps } = register(name);
    const { className: textareaClassName, ...textareaProps } = restProps as any;

    return (
      <div className={className}>
        {showLabel && label && (
          <label htmlFor={name as string} className="block text-sm font-medium text-gray-700 mb-2">
            {label}
          </label>
        )}
        <textarea
          id={name as string}
          {...registerProps}
          {...textareaProps}
          ref={e => {
            registerRef(e);
            if (typeof ref === 'function') {
              ref(e);
            } else if (ref) {
              (ref as React.MutableRefObject<HTMLTextAreaElement | null>).current = e;
            }
          }}
          className={cn(
            'w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 resize-none',
            hasError
              ? 'border-destructive focus:ring-destructive focus:border-destructive'
              : 'border-border focus:ring-primary focus:border-primary',
            textareaClassName
          )}
        />
        {error && <div className="text-destructive text-sm mt-1">{error.message as string}</div>}
      </div>
    );
  }
);

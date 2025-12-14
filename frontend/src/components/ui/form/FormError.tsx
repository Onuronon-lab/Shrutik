import { FieldErrors } from 'react-hook-form';

interface FormErrorProps {
  error?: string | FieldErrors<any> | undefined;
  className?: string;
}

export function FormError({ error, className = '' }: FormErrorProps) {
  if (!error) return null;

  const errorMessage = typeof error === 'string' ? error : 'Please fix the errors above';

  return <div className={`text-destructive text-sm text-center ${className}`}>{errorMessage}</div>;
}

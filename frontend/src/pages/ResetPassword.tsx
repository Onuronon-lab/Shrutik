import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { EyeIcon, EyeSlashIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { authService } from '../services/auth.service';
import { FormInput, FormError } from '../components/ui/form';
import { cn } from '../utils/cn';

type ResetFormData = {
  password: string;
  confirmPassword: string;
};

export const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    setError,
  } = useForm<ResetFormData>({
    mode: 'onBlur',
  });

  const password = watch('password', '');
  const confirmPassword = watch('confirmPassword', '');

  const passwordValidation = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    matches: password === confirmPassword && confirmPassword.length > 0,
  };

  const getPasswordStrength = () => {
    const validCount = Object.values(passwordValidation).filter(Boolean).length - 1;
    if (validCount <= 2) return { label: 'Weak', color: 'bg-red-500', width: '33%' };
    if (validCount <= 4) return { label: 'Medium', color: 'bg-yellow-500', width: '66%' };
    return { label: 'Strong', color: 'bg-green-500', width: '100%' };
  };

  const strength = password.length > 0 ? getPasswordStrength() : null;

  const ValidationItem = ({ isValid, text }: { isValid: boolean; text: string }) => (
    <div className="flex items-center gap-1.5 text-xs">
      {isValid ? (
        <CheckIcon className="h-3.5 w-3.5 text-green-600" />
      ) : (
        <XMarkIcon className="h-3.5 w-3.5 text-gray-400" />
      )}
      <span className={isValid ? 'text-green-600' : 'text-gray-500'}>{text}</span>
    </div>
  );

  const onSubmit = async (data: ResetFormData) => {
    if (!token) {
      setError('root', { message: 'Invalid or expired reset link.' });
      return;
    }

    if (data.password !== data.confirmPassword) {
      setError('confirmPassword', { message: 'Passwords do not match.' });
      return;
    }

    setIsLoading(true);
    try {
      await authService.resetPassword(token, data.password);
      setSuccess('Password updated successfully. Redirecting to login...');
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: any) {
      setError('root', {
        message: err.response?.data?.detail || 'Failed to reset password.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground">
            Create New Password
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            Enter and confirm your new password.
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="rounded-md shadow-sm space-y-2">
            {/* Password */}
            <div className="relative">
              <FormInput
                register={register}
                errors={errors}
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="New Password"
                label="New Password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center px-3 bg-input border-l border-border rounded-r-md text-secondary-foreground hover:text-foreground"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>

            {password.length > 0 && (
              <div className="px-3 py-2 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Password strength</span>
                  <span className="text-xs font-medium">{strength?.label}</span>
                </div>
                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${strength?.color} transition-all duration-300`}
                    style={{ width: strength?.width }}
                  />
                </div>

                <div className="pt-2 space-y-1">
                  <ValidationItem
                    isValid={passwordValidation.minLength}
                    text="At least 8 characters"
                  />
                  <ValidationItem
                    isValid={passwordValidation.hasUppercase}
                    text="One uppercase letter"
                  />
                  <ValidationItem
                    isValid={passwordValidation.hasLowercase}
                    text="One lowercase letter"
                  />
                  <ValidationItem isValid={passwordValidation.hasNumber} text="One number" />
                  <ValidationItem
                    isValid={passwordValidation.hasSpecialChar}
                    text="One special character"
                  />
                </div>
              </div>
            )}

            {/* Confirm */}
            <div className="relative mt-2">
              <FormInput
                register={register}
                errors={errors}
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Confirm Password"
                label="Confirm Password"
                className={cn('rounded-b-md pr-10')}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center px-3 bg-input border-l border-border rounded-r-md text-secondary-foreground hover:text-foreground"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          <FormError error={errors.root?.message} />

          <button
            type="submit"
            disabled={isLoading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
          >
            {isLoading ? 'Updating...' : 'Update Password'}
          </button>
        </form>

        {success && <p className="text-green-600 text-sm text-center font-medium">{success}</p>}
      </div>
    </div>
  );
};

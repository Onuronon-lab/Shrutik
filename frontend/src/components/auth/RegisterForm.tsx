import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { EyeIcon, EyeSlashIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import { SettingsMenu } from '../layout/SettingsMenu';
import { registerSchema, type RegisterFormData } from '../../schemas/auth.schema';
import { FormInput, FormError } from '../ui/form';
import { cn } from '../../utils/cn';

const RegisterForm: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { t } = useTranslation();
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    setError: setFormError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: 'onBlur',
  });

  const password = watch('password', '');

  // Password validation rules
  const passwordValidation = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  // Calculate password strength
  const getPasswordStrength = () => {
    const validCount = Object.values(passwordValidation).filter(Boolean).length;
    if (validCount <= 2)
      return { label: t('signupPage-password-strength-weak'), color: 'bg-red-500', width: '33%' };
    if (validCount <= 4)
      return {
        label: t('signupPage-password-strength-medium'),
        color: 'bg-yellow-500',
        width: '66%',
      };
    return {
      label: t('signupPage-password-strength-strong'),
      color: 'bg-green-500',
      width: '100%',
    };
  };

  const passwordStrength = password.length > 0 ? getPasswordStrength() : null;

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

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setIsLoading(true);
      const success = await registerUser(data.name, data.email, data.password);
      if (success.user) {
        setIsLoading(false);
        navigate('/login', {
          state: {
            message: t('registration_success'),
          },
        });
      }
    } catch (error: any) {
      setIsLoading(false);

      if (error.response) {
        setFormError('root', {
          message: error.response.data?.error.message || 'Server returned an error',
        });
      } else if (error.request) {
        setFormError('root', { message: 'No response from server. It might be offline.' });
      } else {
        setFormError('root', { message: error.message || 'Network Error' });
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-md w-full space-y-8">
        <div className="absolute top-4 right-4">
          <SettingsMenu />
        </div>
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground">
            {t('signupPage-title')}
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            {t('signupPage-subtitle')}
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="rounded-md shadow-sm space-y-2">
            {/* Name */}
            <FormInput
              register={register}
              errors={errors}
              name="name"
              type="text"
              placeholder={t('signupPage-name-label')}
              label={t('signupPage-name-label')}
              className={cn('rounded-t-md')}
            />

            {/* Email */}
            <FormInput
              register={register}
              errors={errors}
              name="email"
              type="email"
              autoComplete="email"
              placeholder={t('signupPage-email-label')}
              label={t('signupPage-email-label')}
            />

            {/* Password */}
            <div className="relative">
              <FormInput
                register={register}
                errors={errors}
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder={t('signupPage-password-label')}
                label={t('signupPage-password-label')}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center px-3 bg-input border-l border-border rounded-r-md text-secondary-foreground hover:text-foreground hover:bg-input/90 transition-colors"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>

            {/* Password Strength Indicator */}
            {password.length > 0 && (
              <div className="px-3 py-2 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">{t('signupPage-password-strength')}</span>
                  <span
                    className={`text-xs font-medium ${
                      passwordStrength?.label === t('signupPage-password-strength-weak')
                        ? 'text-red-600'
                        : passwordStrength?.label === t('signupPage-password-strength-medium')
                          ? 'text-yellow-600'
                          : 'text-green-600'
                    }`}
                  >
                    {passwordStrength?.label}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${passwordStrength?.color} transition-all duration-300`}
                    style={{ width: passwordStrength?.width }}
                  />
                </div>

                <div className="pt-2 space-y-1">
                  <p className="text-xs text-gray-600 font-medium mb-1.5">
                    {t('signupPage-password-must-contain')}
                  </p>
                  <ValidationItem
                    isValid={passwordValidation.minLength}
                    text={t('signupPage-min-chars')}
                  />
                  <ValidationItem
                    isValid={passwordValidation.hasUppercase}
                    text={t('signupPage-one-uppercase')}
                  />
                  <ValidationItem
                    isValid={passwordValidation.hasLowercase}
                    text={t('signupPage-one-lowercase')}
                  />
                  <ValidationItem
                    isValid={passwordValidation.hasNumber}
                    text={t('signupPage-one-number')}
                  />
                  <ValidationItem
                    isValid={passwordValidation.hasSpecialChar}
                    text={t('signupPage-one-special')}
                  />
                </div>
              </div>
            )}

            {/* Confirm Password */}
            <div className="relative mt-2">
              <FormInput
                register={register}
                errors={errors}
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder={t('signupPage-confirm-password-label')}
                label={t('signupPage-confirm-password-label')}
                className={cn('rounded-b-md pr-10')}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center px-3 bg-input border-l border-border rounded-r-md text-secondary-foreground hover:text-foreground hover:bg-input/90 transition-colors"
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

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-active disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('signupPage-registering') : t('signupPage-submit')}
            </button>
          </div>
        </form>

        <div className="mt-2 text-center text-[14px]">
          <span className="text-secondary-foreground">{t('signupPage-login-text')}</span>
          <button
            type="button"
            className="ml-2 text-primary hover:underline font-medium"
            onClick={() => navigate('/login')}
          >
            {t('signupPage-login-link')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RegisterForm;

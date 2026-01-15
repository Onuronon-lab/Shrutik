import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import { SettingsMenu } from '../layout/SettingsMenu';
import { loginSchema, type LoginFormData } from '../../schemas/auth.schema';
import { FormInput, FormError } from '../ui/form';
import { cn } from '../../utils/cn';

const LoginForm: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Show success message from registration redirect
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);

    try {
      const success = await login(data.email, data.password);

      if (success.user) {
        navigate(from, { replace: true });
      } else {
        setFormError('root', { message: 'Invalid email or password' });
      }
    } catch (error: any) {
      // Axios Error Parsing
      if (error.response) {
        setFormError('root', {
          message: error.response.data?.error.message || 'Server returned an error',
        });
      } else if (error.request) {
        setFormError('root', { message: 'No response from server. It might be offline.' });
      } else {
        setFormError('root', { message: error.message || 'Network Error' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-md w-full space-y-8">
        <div className="absolute top-4 right-4">
          <SettingsMenu />
        </div>
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground">
            {t('login-title')}
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            {t('login-subtitle')}
          </p>
        </div>

        {successMessage && (
          <div className="bg-success border border-success-forground text-success-forground px-4 py-3 rounded-md text-sm text-center">
            {successMessage}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="rounded-md shadow-sm space-y-2">
            <FormInput
              register={register}
              errors={errors}
              name="email"
              type="text"
              autoComplete="email"
              placeholder={t('login-email')}
              label={t('login-email')}
              className={cn('rounded-t-md')}
            />

            <div className="relative">
              <FormInput
                register={register}
                errors={errors}
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder={t('login-password')}
                label={t('login-password')}
                className={cn('rounded-b-md pr-10')}
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
          </div>

          <FormError error={errors.root?.message} />

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-primary-foreground bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('login-signingIn') : t('login-signin')}
            </button>
          </div>

          <div className="mt-2 text-[14px] text-center">
            <span className="text-secondary-foreground">{t('login-noAccount')}</span>
            <button
              type="button"
              className="ml-2 text-primary hover:underline font-medium"
              onClick={() => navigate('/register')}
            >
              {t('login-signup')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginForm;

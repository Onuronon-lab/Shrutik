import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useLocation, Link } from 'react-router-dom';
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

  const from = location.state?.from?.pathname || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError: setFormError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setSuccessMessage('');

    try {
      const result = await login(data.email, data.password);

      if (result && result.user) {
        const targetPath = from === '/' || !from ? '/dashboard' : from;
        navigate(targetPath, { replace: true });
      } else {
        setFormError('root', {
          message: 'Login successful, but user profile could not be loaded.',
        });
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail;

      if (error.response?.status === 422) {
        setFormError('root', { message: 'Server configuration error: Invalid data format.' });
      } else if (error.response?.status === 403) {
        setFormError('root', {
          message: errorMessage || 'Account not verified. Please check your email inbox.',
        });
      } else if (error.response?.status === 401) {
        setFormError('root', { message: 'Invalid email or password' });
      } else {
        setFormError('root', {
          message:
            typeof errorMessage === 'string' ? errorMessage : 'An unexpected error occurred.',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-md w-full space-y-8 relative z-10">
        <div className="absolute top-4 right-4">
          <SettingsMenu />
        </div>

        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            {t('login-title')}
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            {t('login-subtitle')}
          </p>
        </div>

        {successMessage && (
          <div className="bg-success/20 border border-success text-success-foreground px-4 py-3 rounded-md text-sm text-center">
            {t(successMessage) || successMessage}
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
              className={cn('rounded-t-md bg-white/5 border-white/10 text-white')}
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
                className={cn('rounded-b-md pr-10 bg-white/5 border-white/10 text-white')}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center px-3 bg-transparent text-secondary-foreground hover:text-white transition-colors"
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

          <div className="flex justify-end -mt-2">
            <Link
              to="/forgot-password"
              className="text-xs font-medium text-primary hover:text-primary-hover hover:underline"
            >
              {t('forgotPassword')}
            </Link>
          </div>

          <FormError error={errors.root?.message} />

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-md text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
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

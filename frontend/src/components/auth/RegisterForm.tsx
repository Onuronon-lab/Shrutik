import React, { useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { EyeIcon, EyeSlashIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { ThemeToggle } from '../layout/ThemeSwitcher';
import { useTranslation } from 'react-i18next';
import LanguageSwitch from '../layout/LanguageSwitcher';

const RegisterForm: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmPasswordTouched, setConfirmPasswordTouched] = useState(false);
  const [nameTouched, setNameTouched] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);

  const { t } = useTranslation();

  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  // Password validation rules
  const passwordValidation = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  };

  const allValidationsPassed = Object.values(passwordValidation).every(Boolean);

  // Email validation
  const isValidEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Calculate password strength
  const getPasswordStrength = () => {
    const validCount = Object.values(passwordValidation).filter(Boolean).length;
    if (validCount <= 2) return { label: 'Weak', color: 'bg-red-500', width: '33%' };
    if (validCount <= 4) return { label: 'Medium', color: 'bg-yellow-500', width: '66%' };
    return { label: 'Strong', color: 'bg-green-500', width: '100%' };
  };

  const passwordStrength = password.length > 0 ? getPasswordStrength() : null;

  // Password mismatch errors
  const passwordErrors: string[] = [];
  if (passwordTouched && password.length > 0 && !allValidationsPassed) {
    if (!passwordValidation.hasUppercase) {
      passwordErrors.push('Password must contain at least one uppercase letter');
    }
    if (!passwordValidation.hasSpecialChar) {
      passwordErrors.push('Password must contain at least one special character (!@#$%^&*...)');
    }
  }

  // Clear all messages reliably
  const clearAllMessages = useCallback(() => {
    setError('');
    setSuccessMessage('');
  }, []);

  // Clear error when any field changes
  const handleFieldChange = (setter: React.Dispatch<React.SetStateAction<string>>, value: string) => {
    setter(value);
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Set all fields as touched to show validation errors
    setNameTouched(true);
    setEmailTouched(true);
    setPasswordTouched(true);
    setConfirmPasswordTouched(true);
    
    // Clear messages using functional updates
    clearAllMessages();

    // Client-side validation
    if (!name.trim()) {
      setError("Please enter your name");
      return;
    }

    if (!email.trim()) {
      setError("Please enter your email");
      return;
    }

    if (!isValidEmail(email)) {
      setError("Please enter a valid email address");
      return;
    }

    if (!allValidationsPassed) {
      setError("Please meet all password requirements");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // If all validations pass, proceed with registration
    await handleRegistration();
  };

  const handleRegistration = async () => {
    try {
      setIsLoading(true);
      const success = await register(name, email, password);
      if (success.user) {
        setIsLoading(false);
        navigate('/login', {
          state: {
            message: t('registration_success')
          }
        });
      }
    } catch (error: any) {
      setIsLoading(false);
      
      // Clear any previous messages before setting new error
      clearAllMessages();
      
      if (error.response) {
        setError(error.response.data?.error.message || "Server returned an error");
      } else if (error.request) {
        setError("No response from server. It might be offline.");
      } else {
        setError(error.message || "Network Error");
      }
      
    }
  };

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

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-md w-full space-y-8">
          <div className="absolute top-4 right-4 flex items-center space-x-2">
              <ThemeToggle className="h-8 w-16 px-1 lg:h-10 lg:w-20 lg:px-2" />
              <LanguageSwitch />
        </div>
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground">
            {t('signupPage-title')}
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            {t('signupPage-subtitle')}
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit} noValidate> {/* Add noValidate to disable browser validation */}
          <div className="rounded-md shadow-sm space-y-2">
            {/* Name */}
            <div>
              <label htmlFor="name" className="sr-only">{t('signupPage-name-label')}</label>
              <input
                id="name"
                name="name"
                type="text"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                  nameTouched && !name.trim() ? 'border-red-500' : 'border-border'
                } placeholder-nutral text-nutral-foreground rounded-t-md focus:outline-none focus:ring-primary focus:border-primary sm:text-sm`}
                placeholder="Name"
                value={name}
                onChange={e => handleFieldChange(setName, e.target.value)}
                onBlur={() => setNameTouched(true)}
              />
              {nameTouched && !name.trim() && (
                <div className="px-3 text-red-600 text-xs mt-1">
                  Please enter your name
                </div>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="sr-only">{t('signupPage-email-label')}</label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                  emailTouched && (!email.trim() || !isValidEmail(email)) ? 'border-red-500' : 'border-border'
                } placeholder-nutral text-nutral-foreground focus:outline-none focus:ring-primary focus:border-primary sm:text-sm`}
                placeholder="Email address"
                value={email}
                onChange={e => handleFieldChange(setEmail, e.target.value)}
                onBlur={() => setEmailTouched(true)}
                // Add autocomplete to prevent browser password management
                autoComplete="email"
              />
              {emailTouched && !email.trim() && (
                <div className="px-3 text-red-600 text-xs mt-1">
                  Please enter your email
                </div>
              )}
              {emailTouched && email.trim() && !isValidEmail(email) && (
                <div className="px-3 text-red-600 text-xs mt-1">
                  Please enter a valid email address
                </div>
              )}
            </div>

            {/* Password */}
            <div className="relative">
              <label htmlFor="password" className="sr-only">{t('signupPage-password-label')}</label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border ${passwordTouched && !allValidationsPassed ? 'border-red-500' : 'border-border'
                  } placeholder-nutral text-nutral-foreground focus:outline-none focus:ring-primary focus:border-primary sm:text-sm`}
                placeholder="Password"
                value={password}
                onChange={e => handleFieldChange(setPassword, e.target.value)}
                onBlur={() => setPasswordTouched(true)}
                // Prevent browser password management
                autoComplete="new-password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeSlashIcon className="h-5 w-5 text-muted-foreground" /> : <EyeIcon className="h-5 w-5 text-muted-foreground" />}
              </button>
            </div>

            {/* Password Strength Indicator */}
            {password.length > 0 && (
              <div className="px-3 py-2 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Password strength:</span>
                  <span className={`text-xs font-medium ${passwordStrength?.label === 'Weak' ? 'text-red-600' :
                      passwordStrength?.label === 'Medium' ? 'text-yellow-600' :
                        'text-green-600'
                    }`}>
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
                  <p className="text-xs text-gray-600 font-medium mb-1.5">Password must contain:</p>
                  <ValidationItem isValid={passwordValidation.minLength} text="At least 8 characters" />
                  <ValidationItem isValid={passwordValidation.hasUppercase} text="One uppercase letter" />
                  <ValidationItem isValid={passwordValidation.hasLowercase} text="One lowercase letter" />
                  <ValidationItem isValid={passwordValidation.hasNumber} text="One number" />
                  <ValidationItem isValid={passwordValidation.hasSpecialChar} text="One special character (!@#$%^&*...)" />
                </div>

                {/* Error messages for missing requirements */}
                {passwordErrors.length > 0 && passwordTouched && (
                  <div className="mt-2 space-y-1">
                    {passwordErrors.map((err, idx) => (
                      <div key={idx} className="text-red-600 text-xs flex items-start gap-1">
                        <span>•</span>
                        <span>{err}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Confirm Password */}
            <div className="relative mt-2">
              <label htmlFor="confirmPassword" className="sr-only">{t('signupPage-confirm-password-label')}</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border ${confirmPasswordTouched && confirmPassword && password !== confirmPassword ? 'border-red-500' : 'border-border'
                  } placeholder-nutral text-nutral-foreground rounded-b-md focus:outline-none focus:ring-primary focus:border-primary sm:text-sm`}
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={e => handleFieldChange(setConfirmPassword, e.target.value)}
                onBlur={() => setConfirmPasswordTouched(true)}
                // Prevent browser password management
                autoComplete="new-password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? <EyeSlashIcon className="h-5 w-5 text-muted-foreground" /> : <EyeIcon className="h-5 w-5 text-muted-foreground" />}
              </button>
            </div>

            {/* Confirm Password Mismatch Error */}
            {confirmPasswordTouched && confirmPassword && password !== confirmPassword && (
              <div className="px-3 text-red-600 text-xs">
                Passwords do not match
              </div>
            )}
          </div>

          {/* Error & Success */}
          {error && (
            <div className="text-red-600 text-sm text-center">
              {error}
            </div>
          )}
          {successMessage && (
            <div className="text-green-600 text-sm text-center">
              {successMessage}
            </div>
          )}

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
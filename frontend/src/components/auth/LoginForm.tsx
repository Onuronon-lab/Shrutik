import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { ThemeToggle } from '../layout/ThemeSwitcher';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  // show success message from registration redirect
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const trimmedEmail = email.trim();  
    if (!/^\S+@\S+\.\S+$/.test(trimmedEmail)) {
      setError('Invalid email format');
      setIsLoading(false);
      return;
    }

    
    const success = await login(trimmedEmail, password);

    if (success) {
      navigate(from, { replace: true });
    } else {
      setError('Invalid email or password');
    }

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-md w-full space-y-8">
        <ThemeToggle className="absolute top-4 right-4 mr-1 h-8 w-16 px-1 lg:h-10 lg:w-20 lg:px-2" />
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground">
            Sign in to Shrutik
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            Help us build better AI with your voice
          </p>
        </div>

        {successMessage && (
          <div className="bg-success border border-success-forground text-success-forground px-4 py-3 rounded-md text-sm text-center">
            {successMessage}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm space-y-2">
            <div>
              <label htmlFor="email" className="sr-only">Email address</label>
              <input
                id="email"
                name="email"
                type="text"
                autoComplete="email"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                  error ? 'border-destructive focus:ring-destructive focus:border-destructive' : 'border-border focus:ring-primary focus:border-primary'
                } placeholder-nutral text-nutral-foreground rounded-t-md focus:outline-none focus:ring-2 sm:text-sm`}
                placeholder="Email address"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (error) setError(''); // Clear error when user starts typing
                }}
              />
            </div>

            <div className="relative">
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border ${
                  error ? 'border-destructive focus:ring-destructive focus:border-destructive' : 'border-border focus:ring-primary focus:border-primary'
                } placeholder-nutral text-nutral-foreground rounded-b-md focus:outline-none focus:ring-2 sm:text-sm`}
                placeholder="Password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (error) setError(''); // Clear error when user starts typing
                }}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="text-destructive text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-primary-foreground bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="mt-2 text-[14px] text-center">
            <span className="text-secondary-foreground">Don't have an account?</span>
            <button
              type="button"
              className="ml-2 text-primary hover:underline font-medium"
              onClick={() => navigate('/register')}
            >
              Sign Up
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginForm;
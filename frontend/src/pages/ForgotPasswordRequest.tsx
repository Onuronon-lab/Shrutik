import { useState } from 'react';
import { authService } from '../services/auth.service';
import { Link } from 'react-router-dom';

export const ForgotPasswordRequest = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await authService.forgotPassword(email);
      setSent(true);
    } catch {
      // Do not reveal whether email exists
      setSent(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-md w-full space-y-8 relative z-10">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">Reset Password</h2>
          <p className="mt-2 text-center text-sm text-secondary-foreground">
            Enter your email and we’ll send you a reset link.
          </p>
        </div>

        {!sent ? (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm space-y-2">
              <div>
                <label className="block text-sm font-medium text-secondary-foreground mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  className="w-full rounded-md px-3 py-2 bg-white/5 border border-white/10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            {error && <p className="text-red-500 text-sm text-center">{error}</p>}

            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-md text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 transition-all"
            >
              {isLoading ? 'Sending...' : 'Send Reset Link'}
            </button>

            <div className="text-center text-[14px]">
              <span className="text-secondary-foreground">Remembered your password?</span>
              <Link to="/login" className="ml-2 text-primary hover:underline font-medium">
                Back to Login
              </Link>
            </div>
          </form>
        ) : (
          <div className="text-center space-y-4">
            <div className="bg-success/20 border border-success text-success-foreground px-4 py-3 rounded-md text-sm">
              If the email address is registered, a password reset link will be delivered to your
              inbox.
            </div>

            <Link to="/login" className="text-primary hover:underline font-medium block pt-2">
              Back to Login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthContextType } from '../types/auth';
import { authService } from '../services/auth.service';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Always start as true to prevent premature redirects

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');

      if (storedToken) {
        setToken(storedToken);
        try {
          // Validate the token and fetch user data immediately
          const response = await authService.validateToken();
          const userData = response.user || response;
          setUser(userData);
        } catch (error) {
          // If validation fails, clear the stale data
          localStorage.removeItem('auth_token');
          setToken(null);
          setUser(null);
        }
      }

      // Stop loading ONLY after we've confirmed the token status
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const result = await authService.login({ email, password });

    if (result.token && result.user) {
      localStorage.setItem('auth_token', result.token);
      setToken(result.token);
      setUser(result.user);
      return result;
    }
  };

  const register = async (name: string, email: string, password: string): Promise<any> => {
    try {
      setIsLoading(true);
      const res = await authService.register({ name, email, password });
      return res;
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

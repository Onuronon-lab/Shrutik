import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthContextType } from '../types/auth';
import { apiService } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    
    if (storedToken) {
      setToken(storedToken);
      validateStoredToken(storedToken); 

    } else {
      setIsLoading(false);
    }

  }, []);
 
  const validateStoredToken = async (storedToken: string) => {
    try {
      const response = await apiService.validateToken();

      
      if (response.token) {
        localStorage.setItem('auth_token', response.token);
        setToken(response.token);
      }

      // Always set the real verified user
      setUser(response.user || response);

      setIsLoading(false);
    } catch (error) {
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      setIsLoading(false);
    }
  };


  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const response = await apiService.login({ email, password });
      
      setUser(response.user);
      setToken(response.token);
      
      localStorage.setItem('auth_token', response.token);
      
      setIsLoading(false);
      return true;
    } catch (error) {
      setIsLoading(false);
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
  };


  const register = async (name: string, email: string, password: string): Promise<boolean> => {
  try {
    setIsLoading(true);
    const response = await apiService.register({ name, email, password }); // apiService.register should return AuthResponse if successful

    setUser(response.user);
    setToken(response.token);

    localStorage.setItem('auth_token', response.token);
    setIsLoading(false);
    return true;
  } catch (error) {
    setIsLoading(false);
    console.error('Registration failed:', error);
    return false;
  }
};


  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    register, 
    isAuthenticated: !!user && !!token,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
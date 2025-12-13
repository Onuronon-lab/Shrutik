import { apiClient } from './apiClient';
import { AuthResponse, LoginCredentials } from '../types/auth';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const loginResponse = await apiClient.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      credentials
    );

    const token = loginResponse.access_token;

    // Temporarily set token to get user info
    const originalAuth = apiClient.api.defaults.headers.Authorization;
    apiClient.api.defaults.headers.Authorization = `Bearer ${token}`;

    try {
      const userResponse = await apiClient.get<any>('/auth/me');

      return {
        user: userResponse,
        token: token,
      };
    } finally {
      if (originalAuth !== undefined) {
        apiClient.api.defaults.headers.Authorization = originalAuth;
      }
    }
  },

  async register(userData: {
    name: string;
    email: string;
    password: string;
  }): Promise<AuthResponse> {
    await apiClient.post('/auth/register', userData);

    return await this.login({
      email: userData.email,
      password: userData.password,
    });
  },

  async validateToken(): Promise<any> {
    return apiClient.get<any>('/auth/me');
  },

  async getCurrentUserStats(): Promise<any> {
    return apiClient.get('/auth/me/stats');
  },
};

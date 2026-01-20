import { apiClient } from './apiClient';
import { AuthResponse, LoginCredentials } from '../types/auth';
import { CurrentUserStats } from '../types/api';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const loginData = await apiClient.post<{ access_token: string; token_type: string }>(
      'auth/login',
      { email: credentials.email, password: credentials.password }
    );

    const accessToken = loginData.access_token;

    // Fetch user data with manual header to ensure success even if interceptor hasn't updated
    const userResponse = await apiClient.api.get<any>('auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    const userData = userResponse.data;

    // Save token after successful fetch
    localStorage.setItem('auth_token', accessToken);

    return {
      user: userData.user || userData,
      token: accessToken,
    };
  },

  async forgotPassword(email: string): Promise<void> {
    const url = `auth/password-reset/request?email=${encodeURIComponent(email)}`;
    await apiClient.post(url, {});
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.api.post('auth/password-reset/confirm', null, {
      params: {
        token: token,
        new_password: newPassword,
      },
    });
  },

  async getCurrentUserStats(): Promise<CurrentUserStats> {
    const token = localStorage.getItem('auth_token');
    try {
      const response = await apiClient.api.get<CurrentUserStats>('auth/me/stats', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { recordings_count: 0, transcriptions_count: 0 } as any;
      }
      throw error;
    }
  },

  async register(userData: { name: string; email: string; password: string }): Promise<void> {
    await apiClient.post('auth/register', userData);
  },

  async validateToken(): Promise<any> {
    return apiClient.get('auth/me');
  },
};

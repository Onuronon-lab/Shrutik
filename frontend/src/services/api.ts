import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { AuthResponse, LoginCredentials } from '../types/auth';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Login returns token directly, not wrapped in ApiResponse
    const loginResponse = await this.api.post<{ access_token: string; token_type: string }>('/auth/login', credentials);

    // Get user info using the token
    const token = loginResponse.data.access_token;

    // Set token temporarily to make the /me request
    const originalAuth = this.api.defaults.headers.Authorization;
    this.api.defaults.headers.Authorization = `Bearer ${token}`;

    try {
      const userResponse = await this.api.get<any>('/auth/me');

      return {
        user: userResponse.data,
        token: token
      };
    } finally {
      // Restore original auth header
      this.api.defaults.headers.Authorization = originalAuth;
    }
  }

  async register(userData: any): Promise<AuthResponse> {
    // Register returns user directly, not wrapped in ApiResponse
    await this.api.post<any>('/auth/register', userData);

    // After registration, we need to login to get the token
    const loginResponse = await this.login({
      email: userData.email,
      password: userData.password
    });

    return loginResponse;
  }

  async validateToken(): Promise<any> {
    const response = await this.api.get<any>('/auth/me');
    return response.data;
  }

  // Generic request methods
  async get<T>(url: string): Promise<T> {
    const response = await this.api.get<T>(url);
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.api.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.api.put<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.api.delete<T>(url);
    return response.data;
  }
}

export const apiService = new ApiService();
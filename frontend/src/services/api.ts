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

  // Script endpoints
  async getRandomScript(duration_category: '2_minutes' | '5_minutes' | '10_minutes', language_id?: number): Promise<any> {
    const params = new URLSearchParams({ duration_category });
    if (language_id) {
      params.append('language_id', language_id.toString());
    }
    return this.get(`/scripts/random?${params.toString()}`);
  }

  // Recording endpoints
  async createRecordingSession(script_id: number, language_id?: number): Promise<any> {
    return this.post('/recordings/sessions', { script_id, language_id });
  }

  async uploadRecording(audioFile: File, uploadData: any): Promise<any> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('session_id', uploadData.session_id);
    formData.append('duration', uploadData.duration.toString());
    formData.append('audio_format', uploadData.audio_format);
    formData.append('file_size', uploadData.file_size.toString());
    
    if (uploadData.sample_rate) {
      formData.append('sample_rate', uploadData.sample_rate.toString());
    }
    if (uploadData.channels) {
      formData.append('channels', uploadData.channels.toString());
    }
    if (uploadData.bit_depth) {
      formData.append('bit_depth', uploadData.bit_depth.toString());
    }

    const response = await this.api.post('/recordings/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getRecordingProgress(recording_id: number): Promise<any> {
    return this.get(`/recordings/${recording_id}/progress`);
  }

  async getUserRecordings(skip = 0, limit = 100, status?: string): Promise<any> {
    const params = new URLSearchParams({ 
      skip: skip.toString(), 
      limit: limit.toString() 
    });
    if (status) {
      params.append('status', status);
    }
    return this.get(`/recordings?${params.toString()}`);
  }
}

export const apiService = new ApiService();
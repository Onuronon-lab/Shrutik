import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { AuthResponse, LoginCredentials } from '../types/auth';
import { TranscriptionSubmission } from '../types/api';
import { DatasetExportRequest, MetadataExportRequest } from '../types/export';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    const baseURL = 'http://localhost:8000/api';
    console.log('API Base URL:', baseURL);
    this.api = axios.create({
      baseURL: baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(config => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      error => {
        if (error.response?.status === 401) {
          // Only redirect to login if we're not already on the login page
          // and if there's a token (meaning it expired)
          const hasToken = localStorage.getItem('auth_token');
          const isLoginPage = window.location.pathname === '/login';

          if (hasToken && !isLoginPage) {
            // Token expired or invalid - redirect to login
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Login returns token directly, not wrapped in ApiResponse
    const loginResponse = await this.api.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      credentials
    );

    // Get user info using the token
    const token = loginResponse.data.access_token;

    // Set token temporarily to make the /me request
    const originalAuth = this.api.defaults.headers.Authorization;
    this.api.defaults.headers.Authorization = `Bearer ${token}`;

    try {
      const userResponse = await this.api.get<any>('/auth/me');

      return {
        user: userResponse.data,
        token: token,
      };
    } finally {
      // Restore original auth header
      this.api.defaults.headers.Authorization = originalAuth;
    }
  }

  async register(userData: any): Promise<AuthResponse> {
    try {
      await this.api.post('/auth/register', userData);

      return await this.login({
        email: userData.email,
        password: userData.password,
      });
    } catch (error: any) {
      console.error('Register API Error:', error);

      const backendError = error.response?.data || { message: 'Unknown server error' };

      throw {
        ...error,
        backend: backendError,
      };
    }
  }

  async validateToken(): Promise<any> {
    const response = await this.api.get<any>('/auth/me');
    return response.data;
  }

  async getCurrentUserStats(): Promise<any> {
    return this.get('/auth/me/stats');
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
  async getRandomScript(
    duration_category: '2_minutes' | '5_minutes' | '10_minutes',
    language_id?: number
  ): Promise<any> {
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
      limit: limit.toString(),
    });
    if (status) {
      params.append('status', status);
    }
    return this.get(`/recordings?${params.toString()}`);
  }

  // Transcription endpoints
  async getRandomChunks(count: number, language_id?: number): Promise<any> {
    const taskRequest = {
      quantity: count,
      language_id: language_id || null,
      skip_chunk_ids: [],
    };
    return this.post('/transcriptions/tasks', taskRequest);
  }

  async submitTranscription(transcription: TranscriptionSubmission): Promise<any> {
    return this.post('/transcriptions/submit', transcription);
  }

  async skipChunk(chunk_id: number): Promise<any> {
    return this.post(`/chunks/${chunk_id}/skip`);
  }

  async getUserTranscriptions(skip = 0, limit = 100): Promise<any> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    return this.get(`/transcriptions?${params.toString()}`);
  }

  async getChunkAudio(chunk_id: number): Promise<string> {
    // Fetch the audio file as a blob and return an object URL
    try {
      const response = await this.api.get(`/chunks/${chunk_id}/audio`, {
        responseType: 'blob',
      });

      // Create an object URL from the blob
      const audioBlob = new Blob([response.data], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);

      return audioUrl;
    } catch (error) {
      console.error('Failed to fetch audio chunk:', error);
      throw error;
    }
  }

  // Admin endpoints
  async getPlatformStats(): Promise<any> {
    return this.get('/admin/stats/platform');
  }

  async getUserStats(limit = 50): Promise<any> {
    return this.get(`/admin/stats/users?limit=${limit}`);
  }

  async getUsersForManagement(role?: string): Promise<any> {
    const params = role ? `?role=${role}` : '';
    return this.get(`/admin/users${params}`);
  }

  async updateUserRole(userId: number, role: string): Promise<any> {
    return this.put(`/admin/users/${userId}/role`, { role });
  }

  async deleteUser(userId: number): Promise<any> {
    return this.delete(`/admin/users/${userId}`);
  }

  async getQualityReviews(limit = 50): Promise<any> {
    return this.get(`/admin/quality-reviews?limit=${limit}`);
  }

  async getFlaggedTranscriptions(limit = 50): Promise<any> {
    return this.get(`/admin/quality-reviews/flagged?limit=${limit}`);
  }

  async createQualityReview(
    transcriptionId: number,
    decision: string,
    rating?: number,
    comment?: string
  ): Promise<any> {
    return this.post(`/admin/quality-reviews/${transcriptionId}`, {
      decision,
      rating,
      comment,
    });
  }

  async getSystemHealth(): Promise<any> {
    return this.get('/admin/system/health');
  }

  async getUsageAnalytics(days = 30): Promise<any> {
    return this.get(`/admin/analytics/usage?days=${days}`);
  }

  // Script management endpoints
  async getScripts(
    skip = 0,
    limit = 100,
    durationCategory?: string,
    languageId?: number
  ): Promise<any> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (durationCategory) {
      params.append('duration_category', durationCategory);
    }
    if (languageId) {
      params.append('language_id', languageId.toString());
    }
    return this.get(`/scripts?${params.toString()}`);
  }

  async getScript(scriptId: number): Promise<any> {
    return this.get(`/scripts/${scriptId}`);
  }

  async createScript(scriptData: any): Promise<any> {
    return this.post('/scripts', scriptData);
  }

  async updateScript(scriptId: number, scriptData: any): Promise<any> {
    return this.put(`/scripts/${scriptId}`, scriptData);
  }

  async deleteScript(scriptId: number): Promise<any> {
    return this.delete(`/scripts/${scriptId}`);
  }

  async validateScript(text: string, durationCategory: string): Promise<any> {
    const params = new URLSearchParams({
      text,
      duration_category: durationCategory,
    });
    return this.post(`/scripts/validate?${params.toString()}`);
  }

  async getScriptStatistics(): Promise<any> {
    return this.get('/scripts/statistics');
  }

  // Export endpoints (Sworik developers only)
  async exportDataset(request: DatasetExportRequest): Promise<any> {
    return this.post('/export/dataset', request);
  }

  async exportMetadata(request: MetadataExportRequest): Promise<any> {
    return this.post('/export/metadata', request);
  }

  async getExportHistory(params?: {
    user_id?: number;
    export_type?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    const queryString = searchParams.toString();
    return this.get(`/export/history${queryString ? `?${queryString}` : ''}`);
  }

  async getSupportedExportFormats(): Promise<any> {
    return this.get('/export/formats');
  }

  async getExportStatistics(): Promise<any> {
    return this.get('/export/stats');
  }
}

export const apiService = new ApiService();

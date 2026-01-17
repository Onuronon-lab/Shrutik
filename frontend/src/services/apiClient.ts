import axios, { AxiosInstance, AxiosResponse } from 'axios';

class ApiClient {
  public api: AxiosInstance;

  constructor() {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
    this.api = axios.create({
      baseURL: baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor: Attach token to every request
    this.api.interceptors.request.use(config => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor: Global error handling
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      error => {
        if (axios.isCancel(error)) {
          return Promise.reject(error);
        }

        // Only redirect on a 401 (Unauthorized) from the server
        if (error.response?.status === 401) {
          const hasToken = localStorage.getItem('auth_token');
          const isLoginPage = window.location.pathname === '/login';

          if (hasToken && !isLoginPage) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

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

  async postFormData<T>(url: string, formData: FormData): Promise<T> {
    const response = await this.api.post<T>(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async getBlob(url: string): Promise<Blob> {
    const response = await this.api.get(url, { responseType: 'blob' });
    return response.data;
  }
}

export const apiClient = new ApiClient();

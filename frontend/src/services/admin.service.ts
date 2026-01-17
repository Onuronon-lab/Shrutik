import { apiClient } from './apiClient';

export const adminService = {
  async getPlatformStats(): Promise<any> {
    return apiClient.get('/admin/stats/platform');
  },

  async getUserStats(limit = 50): Promise<any> {
    return apiClient.get(`/admin/stats/users?limit=${limit}`);
  },

  async getUsersForManagement(role?: string): Promise<any> {
    const params = role ? `?role=${role}` : '';
    return apiClient.get(`/admin/users${params}`);
  },

  async updateUserRole(userId: number, role: string): Promise<any> {
    return apiClient.put(`/admin/users/${userId}/role`, { role });
  },

  async deleteUser(userId: number): Promise<any> {
    return apiClient.delete(`/admin/users/${userId}`);
  },

  async getQualityReviews(limit = 50): Promise<any> {
    return apiClient.get(`/admin/quality-reviews?limit=${limit}`);
  },

  async getFlaggedTranscriptions(limit = 50): Promise<any> {
    return apiClient.get(`/admin/quality-reviews/flagged?limit=${limit}`);
  },

  async createQualityReview(
    transcriptionId: number,
    decision: string,
    rating?: number,
    comment?: string
  ): Promise<any> {
    return apiClient.post(`/admin/quality-reviews/${transcriptionId}`, {
      decision,
      rating,
      comment,
    });
  },

  async getSystemHealth(): Promise<any> {
    return apiClient.get('/admin/system/health');
  },

  async getUsageAnalytics(days = 30): Promise<any> {
    return apiClient.get(`/admin/analytics/usage?days=${days}`);
  },

  async getLanguages(): Promise<Array<{ id: number; name: string; code: string }>> {
    return apiClient.get('/admin/languages');
  },
};

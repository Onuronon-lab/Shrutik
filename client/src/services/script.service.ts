import { apiClient } from './apiClient';

export const scriptService = {
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
    return apiClient.get(`/scripts?${params.toString()}`);
  },

  async getScript(scriptId: number): Promise<any> {
    return apiClient.get(`/scripts/${scriptId}`);
  },

  async createScript(scriptData: any): Promise<any> {
    return apiClient.post('/scripts', scriptData);
  },

  async updateScript(scriptId: number, scriptData: any): Promise<any> {
    return apiClient.put(`/scripts/${scriptId}`, scriptData);
  },

  async deleteScript(scriptId: number): Promise<any> {
    return apiClient.delete(`/scripts/${scriptId}`);
  },

  async validateScript(text: string, durationCategory: string): Promise<any> {
    const params = new URLSearchParams({
      text,
      duration_category: durationCategory,
    });
    return apiClient.post(`/scripts/validate?${params.toString()}`);
  },

  async getScriptStatistics(): Promise<any> {
    return apiClient.get('/scripts/statistics');
  },
};

import { apiClient } from './apiClient';

export const recordingService = {
  async getRandomScript(
    duration_category: '2_minutes' | '5_minutes' | '10_minutes',
    language_id?: number
  ): Promise<any> {
    const params = new URLSearchParams({ duration_category });
    if (language_id) {
      params.append('language_id', language_id.toString());
    }
    return apiClient.get(`/scripts/random?${params.toString()}`);
  },

  async createRecordingSession(script_id: number, language_id?: number): Promise<any> {
    return apiClient.post('/recordings/sessions', { script_id, language_id });
  },

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

    return apiClient.postFormData('/recordings/upload', formData);
  },

  async getRecordingProgress(recording_id: number): Promise<any> {
    return apiClient.get(`/recordings/${recording_id}/progress`);
  },

  async getUserRecordings(skip = 0, limit = 100, status?: string): Promise<any> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (status) {
      params.append('status', status);
    }
    return apiClient.get(`/recordings?${params.toString()}`);
  },
};

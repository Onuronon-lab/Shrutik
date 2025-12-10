import { apiClient } from './apiClient';
import { TranscriptionSubmission } from '../types/api';

export const transcriptionService = {
  async getRandomChunks(count: number, language_id?: number): Promise<any> {
    const taskRequest = {
      quantity: count,
      language_id: language_id || null,
      skip_chunk_ids: [],
    };
    return apiClient.post('/transcriptions/tasks', taskRequest);
  },

  async submitTranscription(transcription: TranscriptionSubmission): Promise<any> {
    return apiClient.post('/transcriptions/submit', transcription);
  },

  async skipChunk(chunk_id: number): Promise<any> {
    return apiClient.post(`/chunks/${chunk_id}/skip`);
  },

  async getUserTranscriptions(skip = 0, limit = 100): Promise<any> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    return apiClient.get(`/transcriptions?${params.toString()}`);
  },

  async getChunkAudio(chunk_id: number): Promise<string> {
    try {
      const blob = await apiClient.getBlob(`/chunks/${chunk_id}/audio`);
      const audioBlob = new Blob([blob], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      return audioUrl;
    } catch (error) {
      console.error('Failed to fetch audio chunk:', error);
      throw error;
    }
  },
};

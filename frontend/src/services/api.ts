/**
 * @deprecated This file is kept for backward compatibility.
 * Please use the new service files:
 * - authService from './auth.service'
 * - transcriptionService from './transcription.service'
 * - recordingService from './recording.service'
 * - adminService from './admin.service'
 * - scriptService from './script.service'
 * - exportService from './export.service'
 */

import { authService } from './auth.service';
import { transcriptionService } from './transcription.service';
import { recordingService } from './recording.service';
import { adminService } from './admin.service';
import { scriptService } from './script.service';
import { exportService } from './export.service';

/**
 * Legacy API service class for backward compatibility
 * @deprecated Use individual service modules instead
 */
class ApiService {
  // Auth endpoints
  async login(credentials: any) {
    return authService.login(credentials);
  }

  async register(userData: any) {
    return authService.register(userData);
  }

  async validateToken() {
    return authService.validateToken();
  }

  async getCurrentUserStats() {
    return authService.getCurrentUserStats();
  }

  // Script endpoints
  async getRandomScript(duration_category: any, language_id?: number) {
    return recordingService.getRandomScript(duration_category, language_id);
  }

  // Recording endpoints
  async createRecordingSession(script_id: number, language_id?: number) {
    return recordingService.createRecordingSession(script_id, language_id);
  }

  async uploadRecording(audioFile: File, uploadData: any) {
    return recordingService.uploadRecording(audioFile, uploadData);
  }

  async getRecordingProgress(recording_id: number) {
    return recordingService.getRecordingProgress(recording_id);
  }

  async getUserRecordings(skip = 0, limit = 100, status?: string) {
    return recordingService.getUserRecordings(skip, limit, status);
  }

  // Transcription endpoints
  async getRandomChunks(count: number, language_id?: number) {
    return transcriptionService.getRandomChunks(count, language_id);
  }

  async submitTranscription(transcription: any) {
    return transcriptionService.submitTranscription(transcription);
  }

  async skipChunk(chunk_id: number) {
    return transcriptionService.skipChunk(chunk_id);
  }

  async getUserTranscriptions(skip = 0, limit = 100) {
    return transcriptionService.getUserTranscriptions(skip, limit);
  }

  async getChunkAudio(chunk_id: number) {
    return transcriptionService.getChunkAudio(chunk_id);
  }

  // Admin endpoints
  async getPlatformStats() {
    return adminService.getPlatformStats();
  }

  async getUserStats(limit = 50) {
    return adminService.getUserStats(limit);
  }

  async getUsersForManagement(role?: string) {
    return adminService.getUsersForManagement(role);
  }

  async updateUserRole(userId: number, role: string) {
    return adminService.updateUserRole(userId, role);
  }

  async deleteUser(userId: number) {
    return adminService.deleteUser(userId);
  }

  async getQualityReviews(limit = 50) {
    return adminService.getQualityReviews(limit);
  }

  async getFlaggedTranscriptions(limit = 50) {
    return adminService.getFlaggedTranscriptions(limit);
  }

  async createQualityReview(
    transcriptionId: number,
    decision: string,
    rating?: number,
    comment?: string
  ) {
    return adminService.createQualityReview(transcriptionId, decision, rating, comment);
  }

  async getSystemHealth() {
    return adminService.getSystemHealth();
  }

  async getUsageAnalytics(days = 30) {
    return adminService.getUsageAnalytics(days);
  }

  // Script management endpoints
  async getScripts(skip = 0, limit = 100, durationCategory?: string, languageId?: number) {
    return scriptService.getScripts(skip, limit, durationCategory, languageId);
  }

  async getScript(scriptId: number) {
    return scriptService.getScript(scriptId);
  }

  async createScript(scriptData: any) {
    return scriptService.createScript(scriptData);
  }

  async updateScript(scriptId: number, scriptData: any) {
    return scriptService.updateScript(scriptId, scriptData);
  }

  async deleteScript(scriptId: number) {
    return scriptService.deleteScript(scriptId);
  }

  async validateScript(text: string, durationCategory: string) {
    return scriptService.validateScript(text, durationCategory);
  }

  async getScriptStatistics() {
    return scriptService.getScriptStatistics();
  }

  // Export endpoints
  async exportDataset(request: any) {
    return exportService.exportDataset(request);
  }

  async exportMetadata(request: any) {
    return exportService.exportMetadata(request);
  }

  async getExportHistory(params?: any) {
    return exportService.getExportHistory(params);
  }

  async getSupportedExportFormats() {
    return exportService.getSupportedExportFormats();
  }

  async getExportStatistics() {
    return exportService.getExportStatistics();
  }

  async createExportBatch(filters?: any) {
    return exportService.createExportBatch(filters);
  }

  async getExportBatch(batchId: string) {
    return exportService.getExportBatch(batchId);
  }

  async listExportBatches(params?: any) {
    return exportService.listExportBatches(params);
  }

  async downloadExportBatch(batchId: string) {
    return exportService.downloadExportBatch(batchId);
  }

  async getDownloadQuota() {
    return exportService.getDownloadQuota();
  }

  async retryExportBatch(batchId: string) {
    return exportService.retryExportBatch(batchId);
  }
}

export const apiService = new ApiService();

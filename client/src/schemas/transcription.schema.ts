import { z } from 'zod';

export const transcriptionSchema = z.object({
  text: z.string().min(1, 'Transcription text is required').trim(),
});

export type TranscriptionFormData = z.infer<typeof transcriptionSchema>;

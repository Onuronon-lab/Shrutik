import { z } from 'zod';

const durationCategoryValues = ['2_minutes', '5_minutes', '10_minutes'] as const;
type DurationCategory = (typeof durationCategoryValues)[number];

const durationCategorySchema = z.custom<DurationCategory>(
  value =>
    typeof value === 'string' &&
    (durationCategoryValues as readonly string[]).includes(value as DurationCategory),
  {
    message: 'Invalid duration category',
  }
);

export const scriptSchema = z.object({
  text: z.string().min(1, 'Script text is required').trim(),
  duration_category: durationCategorySchema,
  language_id: z.coerce.number().int().positive().default(1),
  meta_data: z.record(z.string(), z.any()).default({}),
});

export type ScriptFormData = z.infer<typeof scriptSchema>;

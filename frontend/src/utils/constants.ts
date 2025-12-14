// Application constants

export const QUANTITY_OPTIONS = [
  { value: 2, label: 'transcriptionPage-2-sentences', time: 'transcriptionPage-approx-5-min' },
  { value: 5, label: 'transcriptionPage-5-sentences', time: 'transcriptionPage-approx-10-min' },
  { value: 10, label: 'transcriptionPage-10-sentences', time: 'transcriptionPage-approx-20-min' },
  { value: 15, label: 'transcriptionPage-15-sentences', time: 'transcriptionPage-approx-30-min' },
  { value: 20, label: 'transcriptionPage-20-sentences', time: 'transcriptionPage-approx-40-min' },
] as const;

export const DURATION_CATEGORIES = ['2_minutes', '5_minutes', '10_minutes'] as const;

export const BANGLA_KEYBOARD_LAYOUT = [
  ['১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯', '০'],
  ['ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ'],
  ['ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'থ', 'দ', 'ধ', 'ন'],
  ['প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'শ', 'ষ'],
  ['স', 'হ', 'ড়', 'ঢ়', 'য়', 'ৎ', 'ং', 'ঃ', 'ঁ'],
  ['া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ে', 'ৈ', 'ো', 'ৌ'],
  ['্', '।', '?', '!', ',', ';', ':', '"', "'", ' '],
] as const;

export const API_BASE_URL = 'http://localhost:8000/api';

export const PAGINATION_DEFAULTS = {
  page: 1,
  per_page: 20,
} as const;

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import bn from './locales/bn.json';

const STORAGE_KEY = 'appLanguage';
const savedLanguage = localStorage.getItem(STORAGE_KEY) || 'en';

// Helper to handle JSON imports that might be wrapped in .default in production builds
const resolveResource = (res: any) => {
  if (!res) return {};
  return res.default || res;
};

// Inline critical translations as a high-reliability fallback for production
const loginFallback = {
  'login-title': 'Sign in to Shrutik',
  'login-subtitle': 'Help us build better AI with your voice',
  'login-email': 'Email address',
  'login-password': 'Password',
  'login-signin': 'Sign in',
  'login-signingIn': 'Signing in...',
  'login-noAccount': "Don't have an account?",
  'login-signup': 'Sign Up',
};

i18n.use(initReactI18next).init({
  lng: savedLanguage,
  fallbackLng: 'en',
  debug: true, // Enable debug logging in production to help identify issues
  resources: {
    en: {
      translation: {
        ...loginFallback,
        ...resolveResource(en),
      },
    },
    bn: {
      translation: resolveResource(bn),
    },
  },
  interpolation: {
    escapeValue: false,
  },
  react: {
    useSuspense: false, // Ensure it doesn't wait for internal loading if that's the issue
  },
});

export default i18n;

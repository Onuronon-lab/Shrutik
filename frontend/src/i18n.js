import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import bn from "./locales/bn.json";

i18n
    .use(LanguageDetector) // Detect user language
    .use(initReactI18next) // Pass i18n instance to react-i18next
    .init({
        resources: {
            en: { translation: en },
            bn: { translation: bn },
        },
        fallbackLng: "en", // Default language
        debug: false,
        interpolation: {
            escapeValue: false, // React already escapes output
        },
    });

export default i18n;

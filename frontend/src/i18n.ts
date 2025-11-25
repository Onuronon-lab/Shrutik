import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import bn from "./locales/bn.json";

const savedLanguage = localStorage.getItem("appLanguage") || "en";

i18n
  .use(initReactI18next)
  .init({
    lng: savedLanguage,
    fallbackLng: "en",
    resources: {
      en: { translation: en },
      bn: { translation: bn }
    },
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;

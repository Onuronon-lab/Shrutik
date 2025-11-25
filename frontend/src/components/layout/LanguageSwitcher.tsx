// import React from "react";
// import { useTranslation } from "react-i18next";

// const LanguageSwitch: React.FC = () => {
//   const { i18n } = useTranslation();

//   const toggleLanguage = () => {
//     const newLang = i18n.language === "en" ? "bn" : "en";
//     i18n.changeLanguage(newLang);
//     localStorage.setItem("lang", newLang);
//   };

//   return (
//     <div className="flex items-center">
//       <span className="mr-2 text-sm font-medium">EN</span>
//       <label className="relative inline-flex items-center cursor-pointer">
//         <input
//           type="checkbox"
//           className="sr-only peer"
//           checked={i18n.language === "bn"}
//           onChange={toggleLanguage}
//         />
//         <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-500 transition-colors"></div>
//         <div
//           className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-md peer-checked:translate-x-5 transition-transform"
//         ></div>
//       </label>
//       <span className="ml-2 text-sm font-medium">বাংলা</span>
//     </div>
//   );
// };

// export default LanguageSwitch;
"use client";

import React from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../frontend_lib/utils";

const LanguageSwitch: React.FC<{ className?: string }> = ({ className }) => {
  const { i18n } = useTranslation();
  const isBangla = i18n.language === "bn";

  const toggleLanguage = () => {
    const newLang = isBangla ? "en" : "bn";
    i18n.changeLanguage(newLang);
    localStorage.setItem("lang", newLang);
  };

  return (
    <button
      type="button"
      onClick={toggleLanguage}
      aria-label="Toggle language"
      className={cn(
        "relative flex h-8 w-16 items-center rounded-full bg-muted px-1 ring-1 ring-border transition-all",
        className
      )}
    >
      {/* EN */}
      <span
        className={cn(
          "absolute left-1 text-[10px] font-medium transition-colors",
          !isBangla ? "text-foreground" : "text-muted-foreground"
        )}
      >
        EN
      </span>

      {/* বাংলা */}
      <span
        className={cn(
          "absolute right-1 text-[10px] font-medium transition-colors",
          isBangla ? "text-foreground" : "text-muted-foreground"
        )}
      >
        বাংলা
      </span>

      {/* Slider knob */}
      <div
        className={cn(
          "absolute top-0.5 h-7 w-7 rounded-full bg-background shadow transition-transform duration-300",
          isBangla ? "translate-x-8" : "translate-x-0"
        )}
      />
    </button>
  );
};

export default LanguageSwitch;

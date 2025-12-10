'use client';

import React from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

const LanguageSwitch: React.FC<{ className?: string }> = ({ className }) => {
  const { i18n } = useTranslation();
  const isBangla = i18n.language === 'bn';

  const toggleLanguage = () => {
    const newLang = isBangla ? 'en' : 'bn';
    i18n.changeLanguage(newLang);
    localStorage.setItem('lang', newLang);
  };

  return (
    <button
      type="button"
      onClick={toggleLanguage}
      aria-label="Toggle language"
      className={cn(
        'relative flex h-8 w-16 items-center rounded-full bg-muted px-1 ring-1 ring-border transition-all',
        className
      )}
    >
      {/* EN */}
      <span
        className={cn(
          'absolute left-1 text-[10px] font-medium transition-colors',
          !isBangla ? 'text-foreground' : 'text-muted-foreground'
        )}
      >
        EN
      </span>

      {/* বাংলা */}
      <span
        className={cn(
          'absolute right-1 text-[10px] font-medium transition-colors',
          isBangla ? 'text-foreground' : 'text-muted-foreground'
        )}
      >
        বাংলা
      </span>

      {/* Slider knob */}
      <div
        className={cn(
          'absolute top-0.5 h-7 w-7 rounded-full bg-background shadow transition-transform duration-300',
          isBangla ? 'translate-x-8' : 'translate-x-0'
        )}
      />
    </button>
  );
};

export default LanguageSwitch;

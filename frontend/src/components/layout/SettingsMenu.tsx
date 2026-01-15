import React, { useEffect, useRef, useState } from 'react';
import {
  Cog6ToothIcon,
  MoonIcon,
  SunIcon,
  GlobeAltIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useTheme } from '../../hooks/useTheme';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface SettingsMenuProps {
  className?: string;
  align?: 'left' | 'right';
  buttonClassName?: string;
}

const themeOptions = [
  { value: 'light', label: 'Light', icon: SunIcon },
  { value: 'dark', label: 'Dark', icon: MoonIcon },
] as const;

const languageOptions = [
  { value: 'en', label: 'English', short: 'EN' },
  { value: 'bn', label: 'বাংলা', short: 'BN' },
] as const;

export const SettingsMenu: React.FC<SettingsMenuProps> = ({
  className,
  align = 'right',
  buttonClassName,
}) => {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { theme, setTheme } = useTheme();
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const { logout, isAuthenticated } = useAuth();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const handleThemeChange = (value: 'light' | 'dark') => {
    setTheme(value);
  };

  const handleLanguageChange = (value: 'en' | 'bn') => {
    i18n.changeLanguage(value);
    localStorage.setItem('lang', value);
  };

  const handleLogout = () => {
    if (!isAuthenticated) return;
    logout();
    setOpen(false);
    navigate('/login');
  };

  return (
    <div className={cn('relative z-[100]', className)} ref={menuRef}>
      <button
        type="button"
        aria-label="Open settings"
        onClick={() => setOpen(prev => !prev)}
        className={cn(
          'flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-card text-foreground shadow hover:border-primary transition-colors',
          buttonClassName
        )}
      >
        <Cog6ToothIcon className="h-5 w-5" />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-[9998]" 
            onClick={() => setOpen(false)}
          />
          {/* Dropdown */}
          <div
            className={cn(
              'fixed z-[9999] mt-2 w-60 rounded-2xl border border-border bg-card backdrop-blur-xl shadow-2xl p-4 space-y-4',
              align === 'right' ? 'right-4 top-16' : 'left-4 top-16'
            )}
          >
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-secondary-foreground mb-2">
              <SunIcon className="h-4 w-4 text-primary" />
              <span>Theme</span>
            </div>
            <div className="flex gap-2">
              {themeOptions.map(option => {
                const Icon = option.icon;
                const isActive = theme === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleThemeChange(option.value)}
                    className={cn(
                      'flex-1 flex items-center justify-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border text-secondary-foreground hover:border-primary/60'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-secondary-foreground mb-2">
              <GlobeAltIcon className="h-4 w-4 text-primary" />
              <span>Language</span>
            </div>
            <div className="flex gap-2">
              {languageOptions.map(option => {
                const isActive = i18n.language === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleLanguageChange(option.value)}
                    className={cn(
                      'flex-1 rounded-xl border px-3 py-2 text-sm font-semibold transition-colors',
                      isActive
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border text-secondary-foreground hover:border-primary/60'
                    )}
                  >
                    <div className="text-base">{option.short}</div>
                    <div className="text-[10px] font-normal uppercase tracking-widest text-secondary-foreground">
                      {option.label}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {isAuthenticated && (
            <div className="border-t border-border pt-4">
              <button
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive py-2 text-sm font-semibold hover:bg-destructive/20 transition-colors"
              >
                <ArrowRightOnRectangleIcon className="h-4 w-4" />
                Logout
              </button>
            </div>
          )}
        </div>
        </>
      )}
    </div>
  );
};

export default SettingsMenu;

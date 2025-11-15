"use client";

import React from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";
import { cn } from "../../frontend_lib/utils";
// import { useTheme } from "../../hooks/useTheme";

export const ThemeToggle: React.FC<{ className?: string }> = ({ className }) =>{
  const { theme, setTheme } = useTheme();
  const isDark = theme === "dark";

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className={cn(
        "relative flex h-10 w-20 items-center rounded-full bg-muted px-2 ring-1 ring-border transition-all",
        className
      )}
    >

      <Sun
        className={cn(
          "h-4 w-4 md:h-5 md:w-5 transition-colors",
          !isDark ?"text-foreground": "text-muted-foreground"
        )}
      />
      <Moon
        className={cn(
          "ml-auto h-4 w-4 md:h-5 md:w-5 transition-colors",
          isDark ? "text-foreground" : "text-muted-foreground"
        )}
      />

      <div
        className={cn(
          "absolute top-1 h-6 w-6 md:h-8 md:w-8 rounded-full bg-background shadow flex items-center justify-center transition-transform duration-300",
          isDark ? "translate-x-8" : "translate-x-0"
        )}
      >
        {isDark ? (
          <Moon className="h-4 w-4 md:h-5 md:w-5 text-foreground" />
        ) : (
          <Sun className="h-4 w-4 md:h-5 md:w-5 text-foreground" />
        )}
      </div>
    </button>
  );
}

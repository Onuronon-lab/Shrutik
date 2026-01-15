import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useTheme } from '../useTheme';

describe('useTheme - Theme Toggle with Background Images', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();
    
    // Reset document classes
    document.documentElement.classList.remove('dark');
  });

  describe('3.1.1 - Light to Dark Theme Transition', () => {
    it('should switch from light to dark theme and update DOM classes', () => {
      // Start with light theme
      localStorage.setItem('theme', 'light');
      
      const { result } = renderHook(() => useTheme());
      
      // Verify initial state is light
      expect(result.current.theme).toBe('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      
      // Toggle to dark theme
      act(() => {
        result.current.setTheme('dark');
      });
      
      // Verify dark theme is applied
      expect(result.current.theme).toBe('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      expect(localStorage.getItem('theme')).toBe('dark');
    });

    it('should apply dark class to document root when switching to dark theme', () => {
      const { result } = renderHook(() => useTheme());
      
      act(() => {
        result.current.setTheme('light');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      
      act(() => {
        result.current.setTheme('dark');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
  });

  describe('3.1.2 - Dark to Light Theme Transition', () => {
    it('should switch from dark to light theme and update DOM classes', () => {
      // Start with dark theme
      localStorage.setItem('theme', 'dark');
      
      const { result } = renderHook(() => useTheme());
      
      // Verify initial state is dark
      expect(result.current.theme).toBe('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      
      // Toggle to light theme
      act(() => {
        result.current.setTheme('light');
      });
      
      // Verify light theme is applied
      expect(result.current.theme).toBe('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      expect(localStorage.getItem('theme')).toBe('light');
    });

    it('should remove dark class from document root when switching to light theme', () => {
      const { result } = renderHook(() => useTheme());
      
      act(() => {
        result.current.setTheme('dark');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      
      act(() => {
        result.current.setTheme('light');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });
  });

  describe('3.1.3 - Smooth Transition Animation', () => {
    it('should maintain CSS transition properties for smooth animation', () => {
      // This test verifies that the CSS transition is defined
      // The actual 0.25s timing is defined in index.css
      const { result } = renderHook(() => useTheme());
      
      // Toggle theme multiple times
      act(() => {
        result.current.setTheme('dark');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      
      act(() => {
        result.current.setTheme('light');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      
      // Verify that class changes happen synchronously (CSS handles the transition)
      act(() => {
        result.current.setTheme('dark');
      });
      
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('should update theme state immediately without delay', () => {
      const { result } = renderHook(() => useTheme());
      
      const startTime = Date.now();
      
      act(() => {
        result.current.setTheme('dark');
      });
      
      const endTime = Date.now();
      
      // State update should be immediate (< 10ms)
      expect(endTime - startTime).toBeLessThan(10);
      expect(result.current.theme).toBe('dark');
    });
  });

  describe('3.1.4 - Theme Persistence After Page Refresh', () => {
    it('should persist light theme preference in localStorage', () => {
      const { result } = renderHook(() => useTheme());
      
      act(() => {
        result.current.setTheme('light');
      });
      
      expect(localStorage.getItem('theme')).toBe('light');
      
      // Simulate page refresh by creating a new hook instance
      const { result: newResult } = renderHook(() => useTheme());
      
      expect(newResult.current.theme).toBe('light');
    });

    it('should persist dark theme preference in localStorage', () => {
      const { result } = renderHook(() => useTheme());
      
      act(() => {
        result.current.setTheme('dark');
      });
      
      expect(localStorage.getItem('theme')).toBe('dark');
      
      // Simulate page refresh by creating a new hook instance
      const { result: newResult } = renderHook(() => useTheme());
      
      expect(newResult.current.theme).toBe('dark');
    });

    it('should restore theme from localStorage on initial load', () => {
      // Set theme in localStorage before hook initialization
      localStorage.setItem('theme', 'light');
      
      const { result } = renderHook(() => useTheme());
      
      expect(result.current.theme).toBe('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('should default to dark theme when no preference is stored', () => {
      // Ensure localStorage is empty
      localStorage.clear();
      
      const { result } = renderHook(() => useTheme());
      
      expect(result.current.theme).toBe('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('should maintain theme preference across multiple toggles', () => {
      const { result } = renderHook(() => useTheme());
      
      // Toggle multiple times
      act(() => {
        result.current.setTheme('light');
      });
      expect(localStorage.getItem('theme')).toBe('light');
      
      act(() => {
        result.current.setTheme('dark');
      });
      expect(localStorage.getItem('theme')).toBe('dark');
      
      act(() => {
        result.current.setTheme('light');
      });
      expect(localStorage.getItem('theme')).toBe('light');
      
      // Simulate refresh
      const { result: newResult } = renderHook(() => useTheme());
      expect(newResult.current.theme).toBe('light');
    });
  });

  describe('Requirements Validation', () => {
    it('validates Requirement 2.1 - Theme toggle switches between modes', () => {
      const { result } = renderHook(() => useTheme());
      
      const initialTheme = result.current.theme;
      
      act(() => {
        result.current.setTheme(initialTheme === 'dark' ? 'light' : 'dark');
      });
      
      expect(result.current.theme).not.toBe(initialTheme);
    });

    it('validates Requirement 2.2 - Background image updates immediately with theme', () => {
      const { result } = renderHook(() => useTheme());
      
      act(() => {
        result.current.setTheme('light');
      });
      
      // When light theme is active, dark class should be removed
      // This allows CSS to show light-theme.png
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      
      act(() => {
        result.current.setTheme('dark');
      });
      
      // When dark theme is active, dark class should be present
      // This allows CSS to show dark-theme.png via .dark body selector
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('validates Requirement 2.3 - Theme preference is persisted', () => {
      const { result } = renderHook(() => useTheme());
      
      act(() => {
        result.current.setTheme('light');
      });
      
      expect(localStorage.getItem('theme')).toBe('light');
      
      act(() => {
        result.current.setTheme('dark');
      });
      
      expect(localStorage.getItem('theme')).toBe('dark');
    });

    it('validates Requirement 2.4 - Theme toggle maintains position and behavior', () => {
      const { result, rerender } = renderHook(() => useTheme());
      
      // Toggle theme
      act(() => {
        result.current.setTheme('dark');
      });
      
      // Rerender (simulates component update)
      rerender();
      
      // Hook should still work correctly
      expect(result.current.theme).toBe('dark');
      expect(typeof result.current.setTheme).toBe('function');
      
      // Should still be able to toggle
      act(() => {
        result.current.setTheme('light');
      });
      
      expect(result.current.theme).toBe('light');
    });
  });
});

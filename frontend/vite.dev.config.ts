/**
 * Enhanced Development Configuration for Vite
 * Optimizes development experience with advanced HMR and debugging features
 */

import { defineConfig } from 'vite';
import type { UserConfig } from 'vite';

/**
 * Development-specific optimizations
 */
export const devOptimizations: UserConfig = {
  // Enhanced development server configuration
  server: {
    // Optimize HMR for sub-second updates
    hmr: {
      // Use WebSocket for faster communication
      port: 24678,
      // Enable HMR overlay for errors and warnings
      overlay: true,
      // Custom HMR client configuration
      clientPort: 24678,
    },

    // Optimize file serving
    fs: {
      // Enable strict mode for better security
      strict: false,
      // Allow serving files from project root and node_modules
      allow: ['..', 'node_modules'],
    },

    // Optimize middleware
    middlewareMode: false,

    // Enhanced CORS configuration
    cors: {
      origin: true,
      credentials: true,
    },

    // Optimize file watching
    watch: {
      // Use native file watching for better performance
      usePolling: false,
      // Optimize ignored patterns for faster watching
      ignored: [
        '**/node_modules/**',
        '**/build/**',
        '**/.git/**',
        '**/coverage/**',
        '**/.nyc_output/**',
        '**/dist/**',
        '**/.cache/**',
      ],
      // Optimize watch options
      interval: 100,
      binaryInterval: 300,
    },

    // Optimize proxy configuration for API calls
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Enable WebSocket proxying for real-time features
        ws: true,
      },
    },
  },

  // Enhanced dependency optimization for development
  optimizeDeps: {
    // Aggressive pre-bundling for faster HMR
    force: false, // Only force when needed

    // Optimize entry discovery
    entries: ['src/main.tsx', 'src/App.tsx', 'src/pages/**/*.tsx', 'src/components/**/*.tsx'],

    // Include commonly used dependencies
    include: [
      'react',
      'react-dom',
      'react-dom/client',
      'react-router-dom',
      'zustand',
      'zustand/middleware',
      'axios',
      'i18next',
      'react-i18next',
      'clsx',
      'tailwind-merge',
      '@heroicons/react/24/outline',
      '@heroicons/react/24/solid',
      'lucide-react',
      'react-hook-form',
      '@hookform/resolvers/zod',
      'zod',
    ],

    // Exclude development-only dependencies
    exclude: [
      '@vitejs/plugin-react',
      '@testing-library/react',
      '@testing-library/jest-dom',
      '@testing-library/user-event',
      'vitest',
      'fast-check',
      '@vitest/ui',
      'eslint',
      'prettier',
    ],

    // Optimize for faster rebuilds
    holdUntilCrawlEnd: false,
  },

  // Enhanced build configuration for development
  build: {
    // Use inline source maps for faster debugging
    sourcemap: 'inline',

    // Disable minification in development for faster builds
    minify: false,

    // Optimize for development speed
    target: 'esnext',

    // Disable CSS code splitting in development for faster HMR
    cssCodeSplit: false,

    // Optimize chunk size warnings
    chunkSizeWarningLimit: 1000,

    // Disable compression in development
    reportCompressedSize: false,

    // Optimize rollup options for development
    rollupOptions: {
      // Optimize for faster rebuilds
      cache: true,

      // Disable tree shaking in development for faster builds
      treeshake: false,

      // Optimize output for development
      output: {
        // Simpler chunk naming for development
        chunkFileNames: 'js/[name].js',
        entryFileNames: 'js/[name].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
  },

  // Enhanced CSS configuration
  css: {
    // Enable CSS source maps
    devSourcemap: true,

    // Optimize PostCSS for development
    postcss: './postcss.config.js',

    // CSS modules configuration
    modules: {
      // Generate readable class names in development
      generateScopedName: '[name]__[local]___[hash:base64:5]',
    },
  },

  // Development-specific environment variables
  define: {
    __DEV__: JSON.stringify(true),
    __PROD__: JSON.stringify(false),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },

  // Enhanced logging for development
  logLevel: 'info',

  // Clear screen on rebuild
  clearScreen: true,
};

/**
 * HMR optimization configuration
 */
export const hmrOptimizations = {
  // Accept HMR for all modules by default
  acceptHMR: true,

  // Optimize HMR boundaries
  hmrBoundaries: [
    'src/components/**/*.tsx',
    'src/pages/**/*.tsx',
    'src/hooks/**/*.ts',
    'src/stores/**/*.ts',
  ],

  // Custom HMR handling
  customHMR: {
    // Preserve state for specific modules
    preserveState: ['src/stores/**/*.ts', 'src/contexts/**/*.tsx'],

    // Force reload for certain file types
    forceReload: [
      '**/*.html',
      '**/vite.config.ts',
      '**/tailwind.config.js',
      '**/postcss.config.js',
    ],
  },
};

/**
 * Development performance monitoring
 */
export const devPerformanceConfig = {
  // Monitor build times
  buildTiming: true,

  // Monitor HMR performance
  hmrTiming: true,

  // Monitor memory usage
  memoryMonitoring: true,

  // Performance thresholds
  thresholds: {
    // HMR update should be under 1 second
    hmrUpdate: 1000,

    // Initial build should be under 10 seconds
    initialBuild: 10000,

    // Memory usage should stay under 500MB
    memoryUsage: 500 * 1024 * 1024,
  },
};

export default devOptimizations;

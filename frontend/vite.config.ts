import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import compression from 'vite-plugin-compression';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
  const isDevelopment = mode === 'development';

  return {
    plugins: [
      react({
        // Optimize JSX runtime
        jsxRuntime: 'automatic',
        // Include development helpers in dev mode
        include: '**/*.{jsx,tsx}',
      }),

      // Bundle analyzer removed for production build

      // Compression plugins - only in production
      ...(isProduction
        ? [
            // Gzip compression for production builds
            compression({
              algorithm: 'gzip',
              ext: '.gz',
              threshold: 1024, // Only compress files larger than 1KB
              deleteOriginFile: false,
            }),
            // Brotli compression for better compression ratio
            compression({
              algorithm: 'brotliCompress',
              ext: '.br',
              threshold: 1024,
              deleteOriginFile: false,
            }),
          ]
        : []),
    ],

    // Equivalent to CRA's src alias
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },

    // Development server configuration
    server: {
      port: 3000,
      open: !process.env.DOCKER_ENV, // Don't open browser in Docker
      host: true,
      // Enhanced hot module replacement for sub-second updates
      hmr: {
        overlay: true,
        // Use WebSocket for faster HMR
        port: 24678,
        // Optimize HMR for faster updates
        clientPort: 24678,
      },
      // Enable file system caching for faster subsequent starts
      fs: {
        // Allow serving files from one level up to the project root
        allow: ['..'],
        // Enable strict mode for better security and caching
        strict: false,
      },
      // Optimize middleware for development performance
      middlewareMode: false,
      // Enable CORS for development
      cors: true,
      // Optimize watch options for faster file change detection
      watch: {
        // Use polling for better cross-platform compatibility
        usePolling: false,
        // Optimize ignored patterns
        ignored: ['**/node_modules/**', '**/build/**', '**/.git/**'],
      },
    },

    // Optimize dependencies - aggressive pre-bundling with caching
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'zustand',
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
      exclude: [
        '@vitejs/plugin-react',
        '@testing-library/react',
        '@testing-library/jest-dom',
        '@testing-library/user-event',
        'vitest',
        'fast-check',
        '@vitest/ui',
      ],
      // Force optimization of these packages for consistent caching
      force: isDevelopment,
      // Enable dependency caching for faster subsequent builds
      holdUntilCrawlEnd: false,
      // Optimize entry discovery
      entries: ['src/main.tsx', 'src/App.tsx', 'src/pages/**/*.tsx'],
    },

    // Caching strategies for faster subsequent builds
    cacheDir: 'node_modules/.vite',

    // Build configuration with performance monitoring
    build: {
      outDir: 'build',
      // Enhanced source maps for better debugging experience
      sourcemap: isDevelopment ? 'inline' : 'hidden',
      // Enhanced chunk splitting for better code splitting
      rollupOptions: {
        // Add performance monitoring
        onwarn(warning, warn) {
          // Log performance warnings for optimization insights
          if (warning.code === 'CIRCULAR_DEPENDENCY') {
            console.warn(`⚠️  Circular dependency detected: ${warning.message}`);
          }
          if (warning.code === 'UNUSED_EXTERNAL_IMPORT') {
            console.warn(`⚠️  Unused external import: ${warning.message}`);
          }
          if (warning.code === 'LARGE_BUNDLE') {
            console.warn(`⚠️  Large bundle detected: ${warning.message}`);
          }
          warn(warning);
        },

        // Enable aggressive tree shaking
        treeshake: {
          moduleSideEffects: false,
          propertyReadSideEffects: false,
          tryCatchDeoptimization: false,
          unknownGlobalSideEffects: false,
        },
        output: {
          manualChunks: id => {
            // Vendor chunks - more granular splitting
            if (id.includes('node_modules')) {
              // React core - keep together for better caching
              if (id.includes('react') || id.includes('react-dom')) {
                return 'react-vendor';
              }
              // Router - separate chunk for route-based loading
              if (id.includes('react-router')) {
                return 'router-vendor';
              }
              // UI libraries - group related UI components
              if (id.includes('@heroicons') || id.includes('lucide-react')) {
                return 'ui-vendor';
              }
              // Form libraries - group form-related dependencies
              if (
                id.includes('react-hook-form') ||
                id.includes('@hookform') ||
                id.includes('zod')
              ) {
                return 'form-vendor';
              }
              // State management - lightweight, separate chunk
              if (id.includes('zustand')) {
                return 'state-vendor';
              }
              // Internationalization - merge with vendor since it's small
              if (id.includes('i18next')) {
                return 'vendor';
              }
              // HTTP client - separate for API-related functionality
              if (id.includes('axios')) {
                return 'http-vendor';
              }
              // CSS utilities - separate for styling
              if (id.includes('clsx') || id.includes('tailwind-merge')) {
                return 'css-vendor';
              }
              // Testing libraries - should not be in production build
              if (
                id.includes('@testing-library') ||
                id.includes('vitest') ||
                id.includes('fast-check')
              ) {
                return 'test-vendor';
              }
              // Other vendors - catch-all for remaining dependencies
              return 'vendor';
            }

            // Application chunks - feature-based splitting
            if (id.includes('/src/pages/')) {
              return 'pages';
            }
            if (id.includes('/src/components/admin/')) {
              return 'admin-components';
            }
            if (id.includes('/src/components/recording/')) {
              return 'recording-components';
            }
            if (id.includes('/src/components/transcription/')) {
              return 'transcription-components';
            }
            if (id.includes('/src/components/export/')) {
              return 'export-components';
            }
            if (id.includes('/src/features/export/')) {
              return 'export-features';
            }
            if (id.includes('/src/stores/')) {
              return 'stores';
            }
            if (id.includes('/src/hooks/')) {
              return 'hooks';
            }
            if (id.includes('/src/services/')) {
              return 'services';
            }
            if (id.includes('/src/utils/')) {
              return 'utils';
            }

            // Default chunk
            return undefined;
          },
          // Optimize chunk sizes and naming
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: assetInfo => {
            if (!assetInfo.name) return 'assets/[name]-[hash].[ext]';

            const info = assetInfo.name.split('.');
            const ext = info[info.length - 1];
            if (ext && /png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
              return `images/[name]-[hash].[ext]`;
            }
            if (ext && /css/i.test(ext)) {
              return `css/[name]-[hash].[ext]`;
            }
            return `assets/[name]-[hash].[ext]`;
          },
        },
        // External dependencies that should not be bundled
        external: id => {
          // Don't bundle test dependencies in production
          if (process.env.NODE_ENV === 'production') {
            return (
              id.includes('@testing-library') ||
              id.includes('vitest') ||
              id.includes('fast-check') ||
              id.includes('@vitest')
            );
          }
          return false;
        },
      },
      // Optimize build performance and output
      target: 'esnext',
      // Enable CSS code splitting
      cssCodeSplit: true,
      // Optimize asset inlining - smaller threshold for better caching
      assetsInlineLimit: 2048,
      // Set chunk size warnings - more aggressive
      chunkSizeWarningLimit: 500,
      // Enable compression
      reportCompressedSize: true,
      // Optimize for modern browsers
      modulePreload: {
        polyfill: false,
      },
      // Additional optimizations
      emptyOutDir: true,
      // Optimize CSS
      cssMinify: 'esbuild',
      // Optimize for production - use esbuild minification options
      minify: isProduction ? 'esbuild' : false,
      // Enable build performance monitoring
      ...(isProduction && {
        // Log build performance metrics
        write: true,
        // Enable build time analysis
        reportCompressedSize: true,
      }),
    },

    // Public directory configuration
    publicDir: 'public',

    // Environment variables configuration
    envPrefix: 'VITE_',

    // CSS configuration
    css: {
      postcss: './postcss.config.js',
    },

    // Define global constants (equivalent to CRA's process.env)
    define: {
      'process.env': {},
      // Add build-time constants for performance monitoring
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
      __DEV__: JSON.stringify(isDevelopment),
      __PROD__: JSON.stringify(isProduction),
    },

    // Performance monitoring and logging
    logLevel: isDevelopment ? 'info' : 'warn',

    // Clear screen on rebuild in development
    clearScreen: isDevelopment,
  };
});

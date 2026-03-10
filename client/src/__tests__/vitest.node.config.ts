/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    // Don't use setupFiles for Node.js tests to avoid browser-specific mocks
  },
});

/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    // Test environment
    environment: 'jsdom',
    
    // Global test setup
    setupFiles: ['./src/test/setup.ts'],
    
    // Include patterns
    include: [
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'src/**/__tests__/**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    
    // Exclude patterns
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache',
      'build',
      'coverage'
    ],
    
    // Global test configuration
    globals: true,
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/test/',
        'src/**/*.d.ts',
        'src/**/*.config.ts',
        'src/**/*.config.js',
        'src/vite-env.d.ts',
        'src/main.tsx',
        '**/*.test.{ts,tsx,js,jsx}',
        '**/*.spec.{ts,tsx,js,jsx}',
        '**/index.ts',
        'src/types/',
        'public/',
        'dist/',
        'coverage/',
        '.vscode/',
        '.git/'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    
    // Test timeout
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // Watch options
    watchExclude: ['node_modules/**', 'dist/**', 'coverage/**'],
    
    // Reporter configuration
    reporters: ['verbose', 'json', 'html'],
    outputFile: {
      json: './test-results/results.json',
      html: './test-results/index.html'
    },
    
    // Mock configuration
    deps: {
      inline: ['@testing-library/jest-dom']
    },
    
    // Environment variables for tests
    env: {
      NODE_ENV: 'test',
      VITE_API_URL: 'http://localhost:3001',
      VITE_WS_URL: 'ws://localhost:3001',
      VITE_APP_NAME: 'Multi-Bot RAG Platform Test',
      VITE_ENABLE_ANALYTICS: 'false',
      VITE_ENABLE_LOGGING: 'false',
      VITE_LOG_LEVEL: 'error'
    }
  },
  
  // Resolve configuration for tests
  resolve: {
    alias: {
      '@': './src',
      '@/components': './src/components',
      '@/hooks': './src/hooks',
      '@/services': './src/services',
      '@/utils': './src/utils',
      '@/types': './src/types',
      '@/config': './src/config',
      '@/layouts': './src/layouts',
      '@/pages': './src/pages',
      '@/test': './src/test'
    }
  },
  
  // Define configuration for different environments
  define: {
    __TEST__: true,
    __DEV__: false,
    __PROD__: false
  }
});
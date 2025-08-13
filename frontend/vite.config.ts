import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command, mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, '', '');
  
  const isProduction = mode === 'production';
  const isDevelopment = mode === 'development';

  return {
    plugins: [
      react({
        // Optimize JSX in production
        jsxRuntime: 'automatic',
      }),
    ],

    // Path resolution
    resolve: {
      alias: {
        '@': '/src',
        '@components': '/src/components',
        '@hooks': '/src/hooks',
        '@utils': '/src/utils',
        '@services': '/src/services',
        '@types': '/src/types',
        '@config': '/src/config',
        '@styles': '/src/styles',
        '@assets': '/src/assets',
      },
    },

    // Development server configuration
    server: {
      host: '0.0.0.0',
      port: 3000,
      open: false,
      cors: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://backend:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },

    // Preview server configuration
    preview: {
      host: '0.0.0.0',
      port: 3000,
      cors: true,
    },

    // Build configuration
    build: {
      target: 'es2020',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: isProduction ? 'hidden' : true,
      minify: isProduction ? 'esbuild' : false,
      
      // Chunk splitting strategy
      rollupOptions: {
        output: {
          manualChunks: {
            // Vendor chunks
            'react-vendor': ['react', 'react-dom'],
            'router-vendor': ['react-router-dom'],
            'query-vendor': ['@tanstack/react-query'],
          },
          
          // Asset naming
          chunkFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') || [];
            const ext = info[info.length - 1];
            
            if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name || '')) {
              return `assets/images/[name]-[hash].${ext}`;
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
              return `assets/fonts/[name]-[hash].${ext}`;
            }
            if (/\.css$/i.test(assetInfo.name || '')) {
              return `assets/css/[name]-[hash].${ext}`;
            }
            return `assets/[name]-[hash].${ext}`;
          },
        },
      },

      // Build optimizations
      cssCodeSplit: true,
      cssMinify: isProduction,
      
      // Asset handling
      assetsInlineLimit: 4096, // 4kb
      
      // Compression and optimization
      reportCompressedSize: isProduction,
      chunkSizeWarningLimit: 1000, // 1MB warning threshold
    },

    // CSS configuration
    css: {
      modules: {
        localsConvention: 'camelCaseOnly',
        generateScopedName: isDevelopment 
          ? '[name]__[local]___[hash:base64:5]'
          : '[hash:base64:8]',
      },
      devSourcemap: isDevelopment,
    },

    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify('1.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
      __COMMIT_HASH__: JSON.stringify('unknown'),
    },

    // Optimization
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@tanstack/react-query',
      ],
      exclude: ['@vite/client', '@vite/env'],
    },

    // ESBuild configuration
    esbuild: {
      drop: isProduction ? ['console', 'debugger'] : [],
      legalComments: 'none',
    },

    // Worker configuration
    worker: {
      format: 'es',
    },
  };
});
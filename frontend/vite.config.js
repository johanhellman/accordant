import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Remove crossorigin attribute from CSS links (not needed for same-origin resources)
    // Remove crossorigin from css plugin removed to prevent HTML corruption
  ],
  base: '/', // Ensure assets are served from root path
  build: {
    assetsDir: 'assets',
    outDir: 'dist',
    // Ensure proper module loading for production
    rollupOptions: {
      output: {
        // Ensure consistent chunking
        manualChunks: undefined,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.config.js',
      ],
    },
  },
})

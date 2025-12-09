import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Remove crossorigin attribute and ensure CSS loads before scripts
    {
      name: 'fix-asset-loading',
      enforce: 'post',
      apply: 'build',
      transformIndexHtml(html) {
        // Remove crossorigin from link tags (CSS files) and script tags (JS modules)
        html = html.replace(/<link([^>]*)\scrossorigin([^>]*)>/gi, '<link$1$2>')
        html = html.replace(/<script([^>]*)\scrossorigin([^>]*)>/gi, '<script$1$2>')
        
        // Move CSS link to <head> BEFORE script tags and ensure it loads synchronously
        // This is critical for production builds where CSS must load before React renders
        // Find CSS link (may have whitespace/newlines)
        const cssLinkMatch = html.match(/<link[^>]*rel\s*=\s*["']stylesheet["'][^>]*>/i)
        // Find first script tag with type="module"
        const scriptMatch = html.match(/<script[^>]*type\s*=\s*["']module["'][^>]*>/i)
        
        if (cssLinkMatch && scriptMatch) {
          const cssLink = cssLinkMatch[0]
          const scriptTag = scriptMatch[0]
          
          // Remove CSS link from current position (handle whitespace)
          html = html.replace(/<link[^>]*rel\s*=\s*["']stylesheet["'][^>]*>\s*/i, '')
          
          // Insert CSS link immediately before script tag
          // Ensure CSS loads synchronously by placing it before async module script
          html = html.replace(scriptTag, cssLink + '\n    ' + scriptTag)
        }
        
        // Also ensure CSS link is in <head> section (not after </head>)
        const headEndMatch = html.match(/<\/head>/i)
        if (headEndMatch && cssLinkMatch) {
          // If CSS link somehow ended up after </head>, move it back
          const afterHead = html.substring(html.indexOf('</head>') + 7)
          if (afterHead.match(/<link[^>]*rel\s*=\s*["']stylesheet["'][^>]*>/i)) {
            // CSS is after </head>, move it before </head>
            const cssAfterHead = afterHead.match(/<link[^>]*rel\s*=\s*["']stylesheet["'][^>]*>/i)[0]
            html = html.replace('</head>', '    ' + cssAfterHead + '\n  </head>')
            html = html.replace(afterHead.match(/<link[^>]*rel\s*=\s*["']stylesheet["'][^>]*>/i)[0], '')
          }
        }
        
        return html
      },
    },
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

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow external connections (needed for Docker)
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Backend API URL
        changeOrigin: true,
        secure: false,
        // Note: In Docker, the frontend uses VITE_API_URL env var directly in api.js
        // This proxy is mainly for local development
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})



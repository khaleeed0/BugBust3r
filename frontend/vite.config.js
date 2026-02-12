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
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.warn('[Vite proxy] Backend not reachable at 127.0.0.1:8000 - is start-backend.bat running?', err.message)
          })
        },
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})



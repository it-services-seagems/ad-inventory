import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Allow overriding the proxy target with VITE_API_TARGET in .env files
  const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:42057'

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0', // ← Importante!
      port: 42056,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
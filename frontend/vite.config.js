import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/logout': 'http://127.0.0.1:5000',
      '/simulation/workplace/start': 'http://127.0.0.1:5000',
      '^/simulation/attempts/[^/]+/interview/start$': 'http://127.0.0.1:5000',
      '/static': 'http://127.0.0.1:5000',
    },
  },
})

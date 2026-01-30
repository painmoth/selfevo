import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,  // 支持WebSocket代理
      },
      '/img_src': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})

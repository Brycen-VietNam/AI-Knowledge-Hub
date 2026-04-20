import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],
  envPrefix: ['VITE_'],
  root: fileURLToPath(new URL('.', import.meta.url)),
  server: {
    proxy: {
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    root: fileURLToPath(new URL('.', import.meta.url)),
    environment: 'jsdom',
    globals: true,
    setupFiles: [fileURLToPath(new URL('./tests/setup.ts', import.meta.url))],
  },
})

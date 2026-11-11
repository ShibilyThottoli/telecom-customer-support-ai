import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), '')

  if (mode === 'production' && !env.VITE_API_URL) {
    throw new Error('Set VITE_API_URL to the deployed FastAPI URL before building for production.')
  }

  return {
    plugins: [react()],
  }
})

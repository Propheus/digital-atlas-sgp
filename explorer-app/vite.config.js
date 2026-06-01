import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/',
  plugins: [react()],
  server: { port: 16070, host: '0.0.0.0' },
  preview: { port: 16070, host: '0.0.0.0' },
})

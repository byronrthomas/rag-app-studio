import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';

declare const __dirname: string; // Add this line

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: resolve(__dirname, 'apps/runner'),
  build: {
    outDir: resolve(__dirname, 'apps/runner/dist'),
    rollupOptions: {
      input: resolve(__dirname, 'apps/runner/index.html'),
    },
  },
  publicDir: resolve(__dirname, 'common/public'),
  resolve: {
    alias: {
      '@common': resolve(__dirname, 'common')
    }
  }
})

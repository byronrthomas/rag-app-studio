import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';

declare const __dirname: string; // Add this line

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: resolve(__dirname, 'apps/builder'),
  build: {
    outDir: resolve(__dirname, 'apps/builder/dist'),
    rollupOptions: {
      input: resolve(__dirname, 'apps/builder/index.html'),
    },
  },
  resolve: {
    alias: {
      '@common': resolve(__dirname, 'common')
    }
  }
})

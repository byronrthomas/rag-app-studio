import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';

declare const __dirname: string; // Add this line

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: resolve(__dirname, 'apps/builder'),
  envDir: resolve(__dirname),
  build: {
    outDir: resolve(__dirname, 'apps/builder/dist'),
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'apps/builder/index.html'),
        evaluation: resolve(__dirname, 'apps/builder/evaluation/index.html'),
      }
    },
  },
  publicDir: resolve(__dirname, 'common/public'),
  resolve: {
    alias: {
      '@common': resolve(__dirname, 'common')
    }
  }
})

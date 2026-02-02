import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
      },
      '/models': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
});

import { defineConfig } from 'astro/config';

export default defineConfig({
  vite: {
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8085',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }
});
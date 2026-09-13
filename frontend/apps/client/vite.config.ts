import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import path from "path"
import tailwindcss from "@tailwindcss/vite"

function apiProxy() {
  return {
    target: 'http://localhost:8000',
    changeOrigin: true,
    bypass: (req: { headers: { accept?: string } }) => {
      if (req.headers.accept?.includes('text/html')) {
        return '/index.html';
      }
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/customers': apiProxy(),
      '/accounts': apiProxy(),
      '/payments': apiProxy(),
      '/account-activity': apiProxy(),
      '/risk-features': apiProxy(),
      '/health': apiProxy(),
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
      '/chat': apiProxy(),
      '/conversations': apiProxy(),
      '/risk-reminders': apiProxy(),
      '/voice': apiProxy(),
      '/tts': apiProxy(),
      '/docs': apiProxy(),
      '/redoc': apiProxy(),
      '/openapi.json': apiProxy(),
    },
  },
})

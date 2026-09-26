import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Куда dev-сервер проксирует /api. В Docker (сервис web-dev) это api-dev:8000 —
// задаётся в docker-compose.yaml. Если запускаете `npm run dev` прямо на хосте,
// по умолчанию идём на localhost:8000 (порт api-dev проброшен на хост).
const API_PROXY_TARGET = process.env.VITE_API_PROXY ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Слушаем все интерфейсы: иначе из контейнера web-dev порт не пробросить на хост
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // Разрешаем любой Host: мини-апп открывают через туннель (tuna, cloudflared, ngrok),
    // у которого случайный домен. Это только для dev-сервера, в prod Vite не участвует.
    allowedHosts: true,
    // Фронт и API на одном адресе, как в prod за Caddy: фронт ходит в относительный /api,
    // поэтому CORS не нужен ни в dev, ни в prod
    proxy: {
      '/api': { target: API_PROXY_TARGET, changeOrigin: true },
    },
  },
  build: {
    // Мини-апп открывается во встроенном WebView MAX. По умолчанию Vite собирает под
    // «baseline widely available» браузеры — обычно этого хватает. Если на старых
    // Android что-то не работает, понизьте target (например, 'es2020')
    sourcemap: false,
  },
})

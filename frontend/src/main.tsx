import '@maxhub/max-ui/dist/styles.css'
import './styles.css'

import { MaxUI } from '@maxhub/max-ui'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'

async function bootstrap() {
  // В MAX нет DevTools. eruda — консоль и сеть прямо на экране телефона.
  // В dev включена всегда, в prod — только при сборке с VITE_ENABLE_ERUDA=true.
  // Динамический импорт: в обычную prod-сборку eruda не попадает.
  if (import.meta.env.DEV || import.meta.env.VITE_ENABLE_ERUDA === 'true') {
    const { default: eruda } = await import('eruda')
    eruda.init()
  }

  // Вне MAX (обычный браузер на localhost) подставляем dev-initData
  if (import.meta.env.DEV) {
    const { installDevBridge } = await import('./max/devBridge')
    await installDevBridge()
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      {/* MaxUI сам определяет платформу (iOS/Android) и тему (светлая/тёмная) */}
      <MaxUI>
        <App />
      </MaxUI>
    </StrictMode>,
  )
}

bootstrap()

/**
 * Типы для window.WebApp (MAX Bridge).
 *
 * Официальных тайпингов у скрипта st.max.ru/js/max-web-app.js нет, поэтому
 * описываем то, что используем, по документации https://dev.max.ru/docs/webapps/bridge.
 * Понадобится новый метод — добавьте его сюда.
 */

export type MaxPlatform = 'ios' | 'android' | 'desktop' | 'web'

export interface MaxInitDataUnsafe {
  query_id?: string
  auth_date?: number
  hash?: string
  user?: {
    id: number
    first_name: string
    last_name?: string | null
    username?: string | null
    language_code?: string | null
    photo_url?: string | null
  }
  chat?: { id: number; type: 'DIALOG' | 'CHAT' | 'CHANNEL' }
  /** payload из ссылки https://max.ru/<bot>?startapp=<payload> */
  start_param?: string
}

export interface MaxBackButton {
  isVisible: boolean
  show(): void
  hide(): void
  onClick(cb: () => void): void
  offClick(cb: () => void): void
}

export interface MaxHapticFeedback {
  impactOccurred(style: 'soft' | 'light' | 'medium' | 'heavy' | 'rigid', disableVibrationFallback?: boolean): Promise<unknown>
  notificationOccurred(type: 'error' | 'success' | 'warning', disableVibrationFallback?: boolean): Promise<unknown>
  selectionChanged(disableVibrationFallback?: boolean): Promise<unknown>
}

export interface MaxWebApp {
  /** Строка для проверки подписи на бэкенде. Именно её шлём в Authorization */
  initData: string
  /** Распарсенные данные. НЕ доверять — только для отображения */
  initDataUnsafe: MaxInitDataUnsafe
  platform: MaxPlatform
  version: string
  BackButton: MaxBackButton
  HapticFeedback: MaxHapticFeedback
  enableClosingConfirmation(): void
  disableClosingConfirmation(): void
  openLink(url: string): void
  openMaxLink(url: string): void
  requestContact(): Promise<{ phone: string; authDate: string; hash: string }>
}

declare global {
  interface Window {
    WebApp?: MaxWebApp
  }
}

/**
 * Тонкая обёртка над window.WebApp.
 *
 * Весь остальной код ходит в MAX только через этот модуль. Плюсы:
 *  - одно место, где живут проверки «а есть ли метод на этой платформе»
 *    (haptic не работает на desktop/web, DeviceStorage — в web и т.д.);
 *  - легко подменить мост в тестах и в dev-режиме браузера.
 */

import type { MaxWebApp } from './types'

export function getWebApp(): MaxWebApp | undefined {
  return window.WebApp
}

/** Открыт ли мини-апп внутри MAX (есть подписанная initData) */
export function isInsideMax(): boolean {
  return Boolean(window.WebApp?.initData)
}

export function getInitData(): string {
  return window.WebApp?.initData ?? ''
}

export function getUnsafeUser() {
  return window.WebApp?.initDataUnsafe?.user
}

export function getStartParam(): string | undefined {
  return window.WebApp?.initDataUnsafe?.start_param || undefined
}

/**
 * Тактильный отклик. Методы возвращают Promise и на неподдерживаемых
 * платформах отклоняются — глушим ошибку, вибрация не критична.
 */
export function haptic(type: 'success' | 'error' | 'warning' = 'success'): void {
  window.WebApp?.HapticFeedback?.notificationOccurred(type)?.catch?.(() => {})
}

export function showBackButton(onClick: () => void): () => void {
  const back = window.WebApp?.BackButton
  if (!back) return () => {}
  back.onClick(onClick)
  back.show()
  // Возвращаем функцию очистки — удобно отдавать её прямо из useEffect
  return () => {
    back.offClick(onClick)
    back.hide()
  }
}

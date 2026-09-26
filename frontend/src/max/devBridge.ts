/**
 * Dev-мост: мини-апп в обычном браузере без MAX.
 *
 * Вне MAX у window.WebApp нет initData, и API ответит 401. В dev-режиме
 * просим бэкенд подписать initData тем же алгоритмом, что и клиент MAX
 * (ручка /api/dev/init-data есть только при APP_ENV=dev), и подставляем её.
 * Так проверка подписи на бэкенде работает по-настоящему и в браузере.
 *
 * В prod-сборку этот файл не попадает: импорт стоит под import.meta.env.DEV.
 */

import type { MaxWebApp } from './types'

export async function installDevBridge(): Promise<void> {
  if (window.WebApp?.initData) return // уже внутри MAX — ничего не делаем

  // ?startapp=promo в адресной строке эмулирует ссылку https://max.ru/<bot>?startapp=promo
  const startParam = new URLSearchParams(location.search).get('startapp') ?? ''
  const res = await fetch(`/api/dev/init-data?start_param=${encodeURIComponent(startParam)}`)
  if (!res.ok) {
    console.warn('[dev-bridge] не удалось получить initData:', res.status)
    return
  }
  const { init_data: initData } = (await res.json()) as { init_data: string }

  // Разбираем так же, как это делает MAX, чтобы initDataUnsafe было правдоподобным
  const params = new URLSearchParams(initData)
  const parse = (key: string) => {
    const value = params.get(key)
    return value ? JSON.parse(value) : undefined
  }

  const noop = () => {}
  const resolved = () => Promise.resolve({})
  const real = window.WebApp

  window.WebApp = {
    platform: 'web',
    version: 'dev',
    enableClosingConfirmation: noop,
    disableClosingConfirmation: noop,
    openLink: (url) => window.open(url, '_blank'),
    openMaxLink: (url) => window.open(url, '_blank'),
    requestContact: () => Promise.reject(new Error('requestContact недоступен вне MAX')),
    HapticFeedback: {
      impactOccurred: resolved,
      notificationOccurred: resolved,
      selectionChanged: resolved,
    },
    BackButton: {
      isVisible: false,
      show: () => console.info('[dev-bridge] BackButton.show()'),
      hide: () => console.info('[dev-bridge] BackButton.hide()'),
      onClick: noop,
      offClick: noop,
    },
    // Если реальный скрипт моста что-то уже создал — его методы важнее заглушек
    ...(real ?? {}),
    initData,
    initDataUnsafe: {
      auth_date: Number(params.get('auth_date')),
      query_id: params.get('query_id') ?? undefined,
      user: parse('user'),
      chat: parse('chat'),
      start_param: params.get('start_param') ?? undefined,
    },
  } satisfies MaxWebApp

  console.info('[dev-bridge] подставлена dev-initData для пользователя', window.WebApp.initDataUnsafe.user)
}

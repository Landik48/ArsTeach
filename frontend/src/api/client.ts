/**
 * HTTP-клиент к нашему бэкенду.
 *
 * API живёт на том же домене под /api (в dev и prod это разруливает Caddy),
 * поэтому CORS не нужен. К каждому запросу добавляем initData — по ней
 * бэкенд проверяет подпись и узнаёт пользователя.
 */

import { getInitData } from '../max/bridge'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `max ${getInitData()}`,
      ...init.headers,
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

// --- Типы ответов (зеркало app/api/schemas.py) ---------------------------------

export interface Me {
  id: number
  first_name: string
  last_name: string | null
  username: string | null
  hello_count: number
  start_param: string | null
  chat_type: string | null
}

export interface HelloResult {
  hello_count: number
  notified: boolean
}

// --- Методы -------------------------------------------------------------------

export const api = {
  me: () => request<Me>('/me'),
  hello: () => request<HelloResult>('/hello', { method: 'POST' }),
}

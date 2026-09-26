/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Включить eruda (консоль на экране) в prod-сборке — для отладки на телефоне */
  readonly VITE_ENABLE_ERUDA?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

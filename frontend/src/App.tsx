/**
 * Корневой компонент: загрузка профиля и простейшая навигация между экранами.
 *
 * Роутер намеренно не подключён. Если он понадобится — берите history-режим
 * (например, createBrowserRouter), а НЕ hash-роутер: MAX передаёт данные
 * запуска во фрагменте URL (#WebAppData=...), и hash-роутер может их затереть.
 */

import { Flex, Panel, Spinner, Typography } from '@maxhub/max-ui'
import { useCallback, useEffect, useState } from 'react'

import { api, type Me } from './api/client'
import { AboutScreen } from './screens/AboutScreen'
import { HomeScreen } from './screens/HomeScreen'

type Screen = 'home' | 'about'

export function App() {
  const [me, setMe] = useState<Me | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [screen, setScreen] = useState<Screen>('home')

  useEffect(() => {
    api.me().then(setMe, (err: Error) => setError(err.message))
  }, [])

  // useCallback: одна и та же функция для BackButton.onClick/offClick
  const goHome = useCallback(() => setScreen('home'), [])

  if (error) {
    return (
      <Panel mode="secondary" centeredX centeredY className="screen">
        <Flex direction="column" align="center" gap={8}>
          <Typography.Title>Не удалось загрузиться</Typography.Title>
          <Typography.Text color="secondary">{error}</Typography.Text>
        </Flex>
      </Panel>
    )
  }

  if (!me) {
    return (
      <Panel mode="secondary" centeredX centeredY className="screen">
        <Spinner size={24} />
      </Panel>
    )
  }

  return screen === 'about' ? (
    <AboutScreen onBack={goHome} />
  ) : (
    <HomeScreen me={me} onOpenAbout={() => setScreen('about')} />
  )
}

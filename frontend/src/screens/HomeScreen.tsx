/**
 * Главный экран hello world.
 *
 * Сценарий: загрузили профиль (/api/me) → жмём кнопку → POST /api/hello →
 * бэкенд увеличивает счётчик в БД и бот пишет сообщение в чат.
 */

import {
  Avatar,
  Button,
  CellHeader,
  CellList,
  CellSimple,
  Container,
  Flex,
  Panel,
  Typography,
} from '@maxhub/max-ui'
import { useState } from 'react'

import { api, type Me } from '../api/client'
import { getWebApp, haptic } from '../max/bridge'

interface Props {
  me: Me
  onOpenAbout: () => void
}

export function HomeScreen({ me: initialMe, onOpenAbout }: Props) {
  const [me, setMe] = useState(initialMe)
  const [sending, setSending] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  const sayHello = async () => {
    setSending(true)
    setStatus(null)
    try {
      const result = await api.hello()
      setMe({ ...me, hello_count: result.hello_count })
      setStatus(
        result.notified
          ? 'Бот отправил сообщение в чат 👌'
          : 'Счётчик обновлён. Сообщение в чат не отправлено (нет MAX_BOT_TOKEN?)',
      )
      haptic('success')
    } catch (err) {
      setStatus(`Ошибка: ${(err as Error).message}`)
      haptic('error')
    } finally {
      setSending(false)
    }
  }

  const webApp = getWebApp()
  const initials = `${me.first_name[0] ?? ''}${me.last_name?.[0] ?? ''}`

  return (
    <Panel mode="secondary" className="screen">
      <Container className="hero">
        <Flex direction="column" align="center" gap={8}>
          <Avatar.Container size={72} form="squircle">
            <Avatar.Text gradient="blue">{initials}</Avatar.Text>
          </Avatar.Container>
          <Typography.Title variant="large-strong">Привет, {me.first_name}!</Typography.Title>
          <Typography.Text color="secondary">Это hello world мини-приложения в MAX</Typography.Text>
        </Flex>
      </Container>

      <CellList mode="island" header={<CellHeader>Данные из initData (проверены бэкендом)</CellHeader>}>
        <CellSimple height="compact" title="user_id" after={me.id} />
        <CellSimple height="compact" title="username" after={me.username ?? '—'} />
        <CellSimple height="compact" title="start_param" after={me.start_param ?? '—'} />
        <CellSimple height="compact" title="Платформа" after={webApp?.platform ?? '—'} />
        <CellSimple height="compact" title="Нажатий «привет»" after={me.hello_count} />
      </CellList>

      <Container className="actions">
        <Flex direction="column" gap={12}>
          <Button size="large" stretched loading={sending} onClick={sayHello}>
            Сказать привет боту
          </Button>
          {status && (
            <Typography.Text color="secondary" className="status">
              {status}
            </Typography.Text>
          )}
          <Button size="large" variant="secondary" stretched onClick={onOpenAbout}>
            Второй экран (кнопка «Назад»)
          </Button>
        </Flex>
      </Container>
    </Panel>
  )
}

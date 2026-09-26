/**
 * Второй экран — пример работы с системной кнопкой «Назад» MAX.
 *
 * Пока экран открыт, в шапке MAX видна стрелка назад; при уходе с экрана
 * обработчик снимается и кнопка прячется (очистка в useEffect).
 */

import { CellHeader, CellList, CellSimple, Panel } from '@maxhub/max-ui'
import { useEffect } from 'react'

import { showBackButton } from '../max/bridge'

export function AboutScreen({ onBack }: { onBack: () => void }) {
  useEffect(() => showBackButton(onBack), [onBack])

  return (
    <Panel mode="secondary" className="screen">
      <CellList mode="island" header={<CellHeader>Из чего собран шаблон</CellHeader>}>
        <CellSimple title="Фронт" subtitle="React + Vite + MAX UI" />
        <CellSimple title="Бэкенд" subtitle="FastAPI + maxapi + SQLAlchemy" />
        <CellSimple title="База" subtitle="PostgreSQL + Alembic" />
        <CellSimple title="Прокси" subtitle="Caddy (HTTPS в prod автоматически)" />
      </CellList>
      <CellList mode="island" header={<CellHeader>Навигация</CellHeader>}>
        <CellSimple
          title="Назад"
          subtitle="Стрелка в шапке MAX или эта ячейка"
          showChevron
          onClick={onBack}
        />
      </CellList>
    </Panel>
  )
}

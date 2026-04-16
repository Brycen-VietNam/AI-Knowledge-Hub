// Task: T003 (S004) — HistoryPanel container component
import { useTranslation } from 'react-i18next'
import { useQueryStore } from '../../store/queryStore'
import { HistoryItem } from './HistoryItem'

export function HistoryPanel() {
  const { history, clearHistory, selectHistory } = useQueryStore()
  const { t } = useTranslation()

  if (history.length === 0) return null

  return (
    <aside aria-label={t('history.title')}>
      <h2>{t('history.title')}</h2>
      <button onClick={clearHistory}>{t('history.clear')}</button>
      <ul>
        {history.map((item) => (
          <HistoryItem key={item.id} item={item} onSelect={selectHistory} />
        ))}
      </ul>
    </aside>
  )
}

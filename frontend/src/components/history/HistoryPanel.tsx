// Task: T003 (S004) — HistoryPanel container component
// Task: S005/T003 — Apply CSS classes to HistoryPanel
import { useTranslation } from 'react-i18next'
import { useQueryStore } from '../../store/queryStore'
import { HistoryItem } from './HistoryItem'

export function HistoryPanel() {
  const { history, clearHistory, selectHistory } = useQueryStore()
  const { t } = useTranslation()

  if (history.length === 0) return null

  return (
    <aside className="history-panel" aria-label={t('history.title')}>
      <div className="history-header">
        <span className="history-title">{t('history.title')}</span>
        <button className="btn-clear" onClick={clearHistory}>{t('history.clear')}</button>
      </div>
      <div className="history-list">
        {history.map((item) => (
          <HistoryItem key={item.id} item={item} onSelect={selectHistory} />
        ))}
      </div>
    </aside>
  )
}

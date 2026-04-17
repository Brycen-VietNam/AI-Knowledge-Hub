// Task: T002 (S004) — HistoryItem presentational component
// Task: S005/T003 — Apply CSS classes; remove inline style
import { QueryHistoryItem } from '../../store/queryStore'

interface Props {
  item: QueryHistoryItem
  onSelect: (item: QueryHistoryItem) => void
}

function truncate(str: string, len = 60): string {
  const chars = [...str]
  return chars.length > len ? chars.slice(0, len).join('') + '\u2026' : str
}

function formatTime(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

export function HistoryItem({ item, onSelect }: Props) {
  return (
    <li role="listitem" className="history-item" onClick={() => onSelect(item)}>
      <div className="history-bullet" />
      <div className="history-content">
        <span data-testid="history-query" className="history-q">{truncate(item.query)}</span>
        <time data-testid="history-time" className="history-time">{formatTime(item.timestamp)}</time>
      </div>
    </li>
  )
}

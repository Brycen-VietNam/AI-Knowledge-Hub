// Task: T002 (S004) — HistoryItem presentational component
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
    <li role="listitem" onClick={() => onSelect(item)} style={{ cursor: 'pointer' }}>
      <span data-testid="history-query">{truncate(item.query)}</span>
      <time data-testid="history-time">{formatTime(item.timestamp)}</time>
    </li>
  )
}

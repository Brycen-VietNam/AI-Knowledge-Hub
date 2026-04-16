// Task: T002 (S003) — ConfidenceBadge — score threshold display
// Decision: D012 — score displayed as % (badge labels are fixed identifiers, not i18n)

interface Props {
  score: number
}

export function ConfidenceBadge({ score }: Props) {
  let label: string
  let className: string

  if (score >= 0.7) {
    label = 'HIGH'
    className = 'bg-green-100 text-green-800'
  } else if (score >= 0.4) {
    label = 'MEDIUM'
    className = 'bg-yellow-100 text-yellow-800'
  } else {
    label = 'LOW'
    className = 'bg-red-100 text-red-800'
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${className}`}>
      {label}
    </span>
  )
}

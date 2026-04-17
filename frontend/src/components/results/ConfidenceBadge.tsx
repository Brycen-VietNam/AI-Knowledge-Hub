// Task: T002 (S003) — ConfidenceBadge — score threshold display
// Task: S004/T002 — Replace Tailwind classes with confidence-badge CSS vars
// Decision: D012 — score displayed as % (badge labels are fixed identifiers, not i18n)

interface Props {
  score: number
}

export function ConfidenceBadge({ score }: Props) {
  let label: string
  let variant: string

  if (score >= 0.7) {
    label = 'HIGH'
    variant = 'high'
  } else if (score >= 0.4) {
    label = 'MEDIUM'
    variant = 'medium'
  } else {
    label = 'LOW'
    variant = 'low'
  }

  return (
    <span className={`confidence-badge ${variant}`}>
      {label}
    </span>
  )
}

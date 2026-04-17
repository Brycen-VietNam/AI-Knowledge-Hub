// Task: T003 (S003) — CitationItem — title + score% + chunk preview
// Task: S004/T004 — Replace Tailwind classes with CSS vars
// Decision: D012 — score as integer % (Math.round); chunk_preview plain text (XSS risk)
import type { Citation } from '../../store/queryStore'

interface Props {
  citation: Citation
}

export function CitationItem({ citation }: Props) {
  const scorePercent = `${Math.round(citation.score * 100)}%`

  return (
    <div data-testid="citation-item" className="source-item">
      <div className="source-meta">
        <span className="source-name">{citation.title}</span>
        <span className="source-score">{scorePercent}</span>
      </div>
      <p data-testid="citation-preview" className="source-preview line-clamp-2">
        {citation.chunk_preview}
      </p>
    </div>
  )
}

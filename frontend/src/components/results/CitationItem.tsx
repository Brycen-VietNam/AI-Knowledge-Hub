// Task: T003 (S003) — CitationItem — title + score% + chunk preview
// Decision: D012 — score as integer % (Math.round); chunk_preview plain text (XSS risk)
import type { Citation } from '../../store/queryStore'

interface Props {
  citation: Citation
}

export function CitationItem({ citation }: Props) {
  const scorePercent = `${Math.round(citation.score * 100)}%`

  return (
    <div data-testid="citation-item" className="flex flex-col gap-1 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm">{citation.title}</span>
        <span className="text-xs text-gray-500 shrink-0">{scorePercent}</span>
      </div>
      <p data-testid="citation-preview" className="text-xs text-gray-600 line-clamp-2">
        {citation.chunk_preview}
      </p>
    </div>
  )
}

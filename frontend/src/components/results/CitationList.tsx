// Task: T004 (S003) — CitationList — collapsed > 3 with show-more toggle
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { CitationItem } from './CitationItem'
import type { Citation } from '../../store/queryStore'

interface Props {
  citations: Citation[]
}

const COLLAPSED_LIMIT = 3

export function CitationList({ citations }: Props) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)

  if (citations.length === 0) return null

  const visible = expanded ? citations : citations.slice(0, COLLAPSED_LIMIT)
  const remaining = citations.length - COLLAPSED_LIMIT

  return (
    <div className="flex flex-col divide-y divide-gray-100">
      {visible.map((c) => (
        <CitationItem key={c.doc_id} citation={c} />
      ))}
      {citations.length > COLLAPSED_LIMIT && (
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="mt-2 text-sm text-blue-600 hover:underline text-left"
        >
          {expanded ? t('results.hide') : t('results.show_more', { count: remaining })}
        </button>
      )}
    </div>
  )
}

// Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S003
// Task: T006 (S003) — AnswerPanel — answer + citations + confidence display
// Decision: D012 — score as %; chunk_preview plain text; D002 — token never in localStorage
import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next'
import { ConfidenceBadge } from './ConfidenceBadge'
import { CitationList } from './CitationList'
import { LowConfidenceWarning } from './LowConfidenceWarning'
import type { Citation } from '../../store/queryStore'

interface Props {
  answer: string
  citations: Citation[]
  confidence: number
  isLoading: boolean
  error: string | null
}

export function AnswerPanel({ answer, citations, confidence, isLoading, error }: Props) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div role="status" className="flex items-center gap-2 py-4 text-gray-500 text-sm">
        <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
        <span>Loading...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert" className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    )
  }

  if (!answer && citations.length === 0) {
    return (
      <p className="text-sm text-gray-500 py-4">{t('results.no_results')}</p>
    )
  }

  return (
    <section className="flex flex-col gap-4">
      {answer && (
        <div className="flex items-center gap-2">
          <ConfidenceBadge score={confidence} />
        </div>
      )}

      {confidence < 0.4 && answer && <LowConfidenceWarning />}

      {answer && (
        <div className="prose prose-sm max-w-none text-gray-800">
          <ReactMarkdown>{answer}</ReactMarkdown>
        </div>
      )}

      {answer && citations.length === 0 && (
        <p className="text-xs text-amber-700">{t('results.no_source_warning')}</p>
      )}

      {citations.length > 0 && <CitationList citations={citations} />}
    </section>
  )
}

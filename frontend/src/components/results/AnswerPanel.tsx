// Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S003
// Task: T006 (S003) — AnswerPanel — answer + citations + confidence display
// Task: S004/T003 — Replace Tailwind classes with CSS vars
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
      <div role="status" className="answer-loading">
        <span className="answer-spinner" />
        <span>Loading...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert" className="answer-error">
        {error}
      </div>
    )
  }

  if (!answer && citations.length === 0) {
    return (
      <p className="answer-empty">{t('results.no_results')}</p>
    )
  }

  return (
    <section className="answer-panel">
      {answer && (
        <div className="answer-meta">
          <ConfidenceBadge score={confidence} />
        </div>
      )}

      {confidence < 0.4 && answer && <LowConfidenceWarning />}

      {answer && (
        <div className="answer-body">
          <div className="answer-text">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        </div>
      )}

      {answer && citations.length === 0 && (
        <p className="answer-no-source">{t('results.no_source_warning')}</p>
      )}

      {citations.length > 0 && <CitationList citations={citations} />}
    </section>
  )
}

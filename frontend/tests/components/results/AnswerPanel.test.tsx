import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AnswerPanel } from '../../../src/components/results/AnswerPanel'
import type { Citation } from '../../../src/store/queryStore'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'results.no_results': 'No relevant documents found.',
        'results.low_confidence_warning': 'This answer has low confidence.',
        'results.no_source_warning': 'No source documents were found for this answer.',
      }
      return map[key] ?? key
    },
  }),
}))

// Mock sub-components to isolate AnswerPanel logic
vi.mock('../../../src/components/results/ConfidenceBadge', () => ({
  ConfidenceBadge: ({ score }: { score: number }) => (
    <span data-testid="confidence-badge">{score >= 0.7 ? 'HIGH' : score >= 0.4 ? 'MEDIUM' : 'LOW'}</span>
  ),
}))

vi.mock('../../../src/components/results/CitationList', () => ({
  CitationList: ({ citations }: { citations: Citation[] }) => (
    <div data-testid="citation-list">{citations.length} citations</div>
  ),
}))

vi.mock('../../../src/components/results/LowConfidenceWarning', () => ({
  LowConfidenceWarning: () => <div data-testid="low-confidence-warning">Low confidence</div>,
}))

const sampleCitations: Citation[] = [
  { doc_id: 'd1', title: 'Doc 1', score: 0.9, chunk_preview: 'preview' },
]

describe('AnswerPanel — loading state', () => {
  it('shows loading indicator when isLoading=true', () => {
    render(
      <AnswerPanel
        answer=""
        citations={[]}
        confidence={0}
        isLoading={true}
        error={null}
      />
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('hides result content when loading', () => {
    render(
      <AnswerPanel answer="some answer" citations={[]} confidence={0.8} isLoading={true} error={null} />
    )
    expect(screen.queryByText('some answer')).toBeNull()
  })
})

describe('AnswerPanel — error state', () => {
  it('shows error message when error is set', () => {
    render(
      <AnswerPanel answer="" citations={[]} confidence={0} isLoading={false} error="Rate limit exceeded." />
    )
    expect(screen.getByText('Rate limit exceeded.')).toBeInTheDocument()
  })

  it('does not render answer or citations on error', () => {
    render(
      <AnswerPanel answer="hidden" citations={sampleCitations} confidence={0.8} isLoading={false} error="error" />
    )
    expect(screen.queryByText('hidden')).toBeNull()
    expect(screen.queryByTestId('citation-list')).toBeNull()
  })
})

describe('AnswerPanel — empty state', () => {
  it('shows no-results message when answer and citations both empty', () => {
    render(
      <AnswerPanel answer="" citations={[]} confidence={0} isLoading={false} error={null} />
    )
    expect(screen.getByText('No relevant documents found.')).toBeInTheDocument()
  })
})

describe('AnswerPanel — answer with no citations', () => {
  it('shows answer and no-source warning when citations empty but answer present', () => {
    render(
      <AnswerPanel answer="Here is the answer." citations={[]} confidence={0.8} isLoading={false} error={null} />
    )
    expect(screen.getByText('Here is the answer.')).toBeInTheDocument()
    expect(screen.getByText('No source documents were found for this answer.')).toBeInTheDocument()
  })

  it('does not show no-results when answer is present', () => {
    render(
      <AnswerPanel answer="Some answer" citations={[]} confidence={0.8} isLoading={false} error={null} />
    )
    expect(screen.queryByText('No relevant documents found.')).toBeNull()
  })
})

describe('AnswerPanel — full results', () => {
  it('renders confidence badge', () => {
    render(
      <AnswerPanel answer="Answer text" citations={sampleCitations} confidence={0.85} isLoading={false} error={null} />
    )
    expect(screen.getByTestId('confidence-badge')).toBeInTheDocument()
  })

  it('renders citation list', () => {
    render(
      <AnswerPanel answer="Answer text" citations={sampleCitations} confidence={0.85} isLoading={false} error={null} />
    )
    expect(screen.getByTestId('citation-list')).toBeInTheDocument()
  })

  it('renders answer text via ReactMarkdown', () => {
    render(
      <AnswerPanel answer="The **answer**." citations={sampleCitations} confidence={0.85} isLoading={false} error={null} />
    )
    // ReactMarkdown renders strong tag for **bold**
    expect(screen.getByText('answer')).toBeInTheDocument()
  })
})

describe('AnswerPanel — LowConfidenceWarning', () => {
  it('shows LowConfidenceWarning when confidence < 0.4', () => {
    render(
      <AnswerPanel answer="ans" citations={sampleCitations} confidence={0.3} isLoading={false} error={null} />
    )
    expect(screen.getByTestId('low-confidence-warning')).toBeInTheDocument()
  })

  it('does NOT show LowConfidenceWarning when confidence >= 0.4', () => {
    render(
      <AnswerPanel answer="ans" citations={sampleCitations} confidence={0.4} isLoading={false} error={null} />
    )
    expect(screen.queryByTestId('low-confidence-warning')).toBeNull()
  })
})

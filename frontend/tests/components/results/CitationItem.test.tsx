import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CitationItem } from '../../../src/components/results/CitationItem'
import type { Citation } from '../../../src/store/queryStore'

const baseCitation: Citation = {
  doc_id: 'doc-001',
  title: 'RBAC Overview',
  score: 0.914,
  chunk_preview: 'Role-based access control (RBAC) is a method of restricting network access.',
}

describe('CitationItem — title', () => {
  it('renders the title', () => {
    render(<CitationItem citation={baseCitation} />)
    expect(screen.getByText('RBAC Overview')).toBeInTheDocument()
  })
})

describe('CitationItem — score formatting', () => {
  it('formats score as integer percent (0.914 → 91%)', () => {
    render(<CitationItem citation={baseCitation} />)
    expect(screen.getByText('91%')).toBeInTheDocument()
  })

  it('formats score 0.7 → 70%', () => {
    render(<CitationItem citation={{ ...baseCitation, score: 0.7 }} />)
    expect(screen.getByText('70%')).toBeInTheDocument()
  })

  it('rounds 0.999 → 100%', () => {
    render(<CitationItem citation={{ ...baseCitation, score: 0.999 }} />)
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('rounds 0.005 → 1%', () => {
    render(<CitationItem citation={{ ...baseCitation, score: 0.005 }} />)
    expect(screen.getByText('1%')).toBeInTheDocument()
  })
})

describe('CitationItem — chunk preview', () => {
  it('renders chunk_preview as plain text', () => {
    render(<CitationItem citation={baseCitation} />)
    expect(screen.getByText(baseCitation.chunk_preview)).toBeInTheDocument()
  })

  it('applies line-clamp-2 class to preview', () => {
    render(<CitationItem citation={baseCitation} />)
    const preview = screen.getByTestId('citation-preview')
    expect(preview.className).toContain('line-clamp-2')
  })
})

describe('CitationItem — testid', () => {
  it('has data-testid="citation-item"', () => {
    render(<CitationItem citation={baseCitation} />)
    expect(screen.getByTestId('citation-item')).toBeInTheDocument()
  })
})

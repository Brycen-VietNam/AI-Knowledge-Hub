import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CitationList } from '../../../src/components/results/CitationList'
import type { Citation } from '../../../src/store/queryStore'

const { mockT } = vi.hoisted(() => ({ mockT: vi.fn((key: string, opts?: Record<string, unknown>) => {
  if (key === 'results.show_more') return `Show ${opts?.count} more`
  if (key === 'results.hide') return 'Hide'
  return key
})}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: mockT }),
}))

function makeCitations(n: number): Citation[] {
  return Array.from({ length: n }, (_, i) => ({
    doc_id: `doc-${i}`,
    title: `Document ${i + 1}`,
    score: 0.9 - i * 0.05,
    chunk_preview: `Preview text for document ${i + 1}`,
  }))
}

describe('CitationList — empty', () => {
  it('renders nothing for empty array', () => {
    const { container } = render(<CitationList citations={[]} />)
    expect(container.firstChild).toBeNull()
  })
})

describe('CitationList — 3 or fewer citations', () => {
  it('renders all 3 items flat', () => {
    render(<CitationList citations={makeCitations(3)} />)
    expect(screen.getAllByTestId('citation-item')).toHaveLength(3)
  })

  it('no show-more button when <= 3', () => {
    render(<CitationList citations={makeCitations(2)} />)
    expect(screen.queryByText(/Show \d+ more/)).toBeNull()
  })

  it('renders single item', () => {
    render(<CitationList citations={makeCitations(1)} />)
    expect(screen.getAllByTestId('citation-item')).toHaveLength(1)
  })
})

describe('CitationList — more than 3 citations (collapsed by default)', () => {
  it('shows only 3 items by default when 5 citations', () => {
    render(<CitationList citations={makeCitations(5)} />)
    expect(screen.getAllByTestId('citation-item')).toHaveLength(3)
  })

  it('show-more button label shows remaining count (5 total → "Show 2 more")', () => {
    render(<CitationList citations={makeCitations(5)} />)
    expect(screen.getByText('Show 2 more')).toBeInTheDocument()
  })

  it('show-more button label for 4 total → "Show 1 more"', () => {
    render(<CitationList citations={makeCitations(4)} />)
    expect(screen.getByText('Show 1 more')).toBeInTheDocument()
  })
})

describe('CitationList — expand/collapse toggle', () => {
  it('clicking show-more reveals all items', () => {
    render(<CitationList citations={makeCitations(5)} />)
    fireEvent.click(screen.getByText('Show 2 more'))
    expect(screen.getAllByTestId('citation-item')).toHaveLength(5)
  })

  it('clicking show-more changes button to Hide', () => {
    render(<CitationList citations={makeCitations(5)} />)
    fireEvent.click(screen.getByText('Show 2 more'))
    expect(screen.getByText('Hide')).toBeInTheDocument()
  })

  it('clicking Hide collapses back to 3 items', () => {
    render(<CitationList citations={makeCitations(5)} />)
    fireEvent.click(screen.getByText('Show 2 more'))
    fireEvent.click(screen.getByText('Hide'))
    expect(screen.getAllByTestId('citation-item')).toHaveLength(3)
  })

  it('toggle cycles: collapsed → expanded → collapsed', () => {
    render(<CitationList citations={makeCitations(5)} />)
    expect(screen.getAllByTestId('citation-item')).toHaveLength(3)
    fireEvent.click(screen.getByText('Show 2 more'))
    expect(screen.getAllByTestId('citation-item')).toHaveLength(5)
    fireEvent.click(screen.getByText('Hide'))
    expect(screen.getAllByTestId('citation-item')).toHaveLength(3)
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { HistoryPanel } from '../../../src/components/history/HistoryPanel'
import { useQueryStore } from '../../../src/store/queryStore'
import { QueryHistoryItem } from '../../../src/store/queryStore'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'history.title') return 'Search History'
      if (key === 'history.clear') return 'Clear History'
      return key
    },
  }),
}))

vi.mock('../../../src/components/history/HistoryItem', () => ({
  HistoryItem: ({ item }: { item: QueryHistoryItem }) => (
    <li data-testid="history-item">{item.query}</li>
  ),
}))

function makeItem(id: string, query: string): QueryHistoryItem {
  return { id, query, answer: 'ans', citations: [], timestamp: new Date() }
}

beforeEach(() => {
  useQueryStore.setState({ history: [] })
})

describe('HistoryPanel — empty state', () => {
  it('renders nothing when history is empty', () => {
    const { container } = render(<HistoryPanel />)
    expect(container.firstChild).toBeNull()
  })
})

describe('HistoryPanel — with items', () => {
  it('renders aside when history has items', () => {
    useQueryStore.setState({ history: [makeItem('1', 'q1')] })
    render(<HistoryPanel />)
    expect(screen.getByRole('complementary')).toBeInTheDocument()
  })

  it('renders one HistoryItem per entry', () => {
    useQueryStore.setState({ history: [makeItem('1', 'q1'), makeItem('2', 'q2')] })
    render(<HistoryPanel />)
    expect(screen.getAllByTestId('history-item')).toHaveLength(2)
  })

  it('calls clearHistory when Clear button clicked', () => {
    const clearHistory = vi.fn()
    useQueryStore.setState({ history: [makeItem('1', 'q1')], clearHistory })
    render(<HistoryPanel />)
    fireEvent.click(screen.getByRole('button', { name: 'Clear History' }))
    expect(clearHistory).toHaveBeenCalled()
  })

  it('renders history.title and history.clear via i18n', () => {
    useQueryStore.setState({ history: [makeItem('1', 'q1')] })
    render(<HistoryPanel />)
    expect(screen.getByText('Search History')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Clear History' })).toBeInTheDocument()
  })
})

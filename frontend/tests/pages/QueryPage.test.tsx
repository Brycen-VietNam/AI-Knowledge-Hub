import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryPage } from '../../src/pages/QueryPage'
import { useQueryStore } from '../../src/store/queryStore'

// Hoist mocks before vi.mock factories
const { mockChangeLanguage, mockSubmitQuery } = vi.hoisted(() => ({
  mockChangeLanguage: vi.fn(),
  mockSubmitQuery: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === 'search.char_count') return `${opts?.count as number}/512`
      if (key === 'search.placeholder') return 'Search knowledge base...'
      if (key === 'search.button') return 'Search'
      if (key === 'lang.selector_label') return 'Language'
      if (key === 'results.no_results') return 'No relevant documents found.'
      return key
    },
  }),
  initReactI18next: { type: '3rdParty', init: vi.fn() },
}))

vi.mock('../../src/i18n', () => ({
  default: {
    language: 'en',
    changeLanguage: mockChangeLanguage,
  },
}))

vi.mock('../../src/components/results/AnswerPanel', () => ({
  AnswerPanel: ({ isLoading, error, answer }: { isLoading: boolean; error: string | null; answer: string }) => (
    <div data-testid="answer-panel">
      {isLoading && <span>Loading...</span>}
      {error && <span>{error}</span>}
      {answer && <span>{answer}</span>}
    </div>
  ),
}))

vi.mock('../../src/components/history/HistoryPanel', () => ({
  HistoryPanel: () => {
    const { history } = useQueryStore()
    if (history.length === 0) return null
    return <aside data-testid="history-panel" />
  },
}))

function renderPage() {
  // Reset store to clean state before each render
  useQueryStore.setState({ query: '', isLoading: false, error: null, result: null, history: [] })
  return render(<QueryPage />)
}

describe('QueryPage — renders', () => {
  it('renders SearchInput', () => {
    renderPage()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders main content area', () => {
    renderPage()
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

  it('renders AnswerPanel', () => {
    renderPage()
    expect(screen.getByTestId('answer-panel')).toBeInTheDocument()
  })
})

describe('QueryPage — onSubmit calls submitQuery', () => {
  it('button is disabled when query is empty', () => {
    renderPage()
    expect(screen.getByRole('button', { name: 'Search' })).toBeDisabled()
  })

  it('button enabled with non-empty query', () => {
    useQueryStore.setState({ query: 'test query', isLoading: false, error: null, result: null, history: [] })
    render(<QueryPage />)
    expect(screen.getByRole('button', { name: 'Search' })).not.toBeDisabled()
  })

  it('clicking Search calls store.submitQuery with query and selected lang', () => {
    const submitQuery = vi.fn().mockResolvedValue(undefined)
    useQueryStore.setState({ query: 'what is RBAC?', isLoading: false, error: null, result: null, history: [], submitQuery })
    render(<QueryPage />)
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(submitQuery).toHaveBeenCalledWith('what is RBAC?', expect.any(String))
  })
})

describe('QueryPage — double-submit blocked', () => {
  it('SearchInput button disabled when isLoading=true', () => {
    useQueryStore.setState({ query: 'some query', isLoading: true, error: null, result: null, history: [] })
    render(<QueryPage />)
    expect(screen.getByRole('button', { name: 'Search' })).toBeDisabled()
  })
})

describe('QueryPage — no localStorage for token', () => {
  it('token is not written to localStorage during query', () => {
    const submitQuery = vi.fn().mockResolvedValue(undefined)
    useQueryStore.setState({ query: 'query test', isLoading: false, error: null, result: null, history: [], submitQuery })
    render(<QueryPage />)
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(localStorage.getItem('token')).toBeNull()
  })
})

describe('QueryPage — HistoryPanel', () => {
  it('does not render HistoryPanel when history is empty', () => {
    renderPage()
    expect(screen.queryByTestId('history-panel')).toBeNull()
  })

  it('renders HistoryPanel after history has items', () => {
    useQueryStore.setState({
      query: '',
      isLoading: false,
      error: null,
      result: null,
      history: [{ id: '1', query: 'q', answer: 'a', citations: [], timestamp: new Date() }],
    })
    render(<QueryPage />)
    expect(screen.getByTestId('history-panel')).toBeInTheDocument()
  })
})

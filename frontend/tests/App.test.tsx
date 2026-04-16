import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../src/App'
import { useAuthStore } from '../src/store/authStore'
import { useQueryStore } from '../src/store/queryStore'

// Hoist mocks before vi.mock factories
const { mockChangeLanguage, mockSetNavigate } = vi.hoisted(() => ({
  mockChangeLanguage: vi.fn(),
  mockSetNavigate: vi.fn(),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === 'search.char_count') return `${opts?.count as number}/512`
      if (key === 'search.placeholder') return 'Search knowledge base...'
      if (key === 'search.button') return 'Search'
      if (key === 'lang.selector_label') return 'Language'
      if (key === 'app.title') return 'Knowledge Hub'
      if (key === 'login.submit') return 'Sign In'
      if (key === 'login.username') return 'Username'
      if (key === 'login.password') return 'Password'
      return key
    },
  }),
  initReactI18next: { type: '3rdParty', init: vi.fn() },
}))

vi.mock('../src/i18n', () => ({
  default: { language: 'en', changeLanguage: mockChangeLanguage },
}))

vi.mock('../src/api/client', () => ({
  setNavigate: mockSetNavigate,
  apiClient: { interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
}))

// App uses useNavigate internally — wrap with MemoryRouter to provide Router context
function renderApp(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App — /query route (unauthenticated)', () => {
  it('redirects to /login when not authenticated', () => {
    useAuthStore.setState({ token: null, username: null, password: null, _refreshTimer: null })
    renderApp('/query')
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
})

describe('App — /query route (authenticated)', () => {
  it('renders QueryPage when authenticated', () => {
    useAuthStore.setState({ token: 'valid-token', username: 'alice', password: 'pw', _refreshTimer: null })
    useQueryStore.setState({ query: '', isLoading: false, error: null, result: null })
    renderApp('/query')
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })
})

describe('App — / redirects to /query', () => {
  it('unauthenticated: / → /login (via /query ProtectedRoute redirect)', () => {
    useAuthStore.setState({ token: null, username: null, password: null, _refreshTimer: null })
    renderApp('/')
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
})

describe('App — /login route', () => {
  it('renders login form at /login', () => {
    useAuthStore.setState({ token: null, username: null, password: null, _refreshTimer: null })
    renderApp('/login')
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../src/App'
import { useAuthStore } from '../src/store/authStore'
import '../src/i18n'

// Mock setNavigate to avoid router-outside-context issues
vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client')
  return { ...actual, setNavigate: vi.fn() }
})

function renderApp(initialEntry = '/') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <App />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useAuthStore.setState({
    token: null,
    username: null,
    isAdmin: false,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

describe('App — routing', () => {
  it('unauthenticated / → shows login form', () => {
    renderApp('/')
    expect(screen.getByLabelText('login-form')).toBeInTheDocument()
  })

  it('unauthenticated unknown route → shows login form', () => {
    renderApp('/unknown')
    expect(screen.getByLabelText('login-form')).toBeInTheDocument()
  })

  it('authenticated admin /dashboard → renders dashboard heading', () => {
    useAuthStore.setState({ token: 'tok', username: 'admin', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    renderApp('/dashboard')
    expect(screen.getByRole('heading')).toBeInTheDocument()
  })
})

describe('App — header', () => {
  it('logout button visible when token is set', () => {
    useAuthStore.setState({ token: 'tok', username: 'admin', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    renderApp('/dashboard')
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
  })

  it('logout button hidden when not authenticated', () => {
    renderApp('/')
    expect(screen.queryByRole('button', { name: /sign out/i })).not.toBeInTheDocument()
  })

  it('logout clears store on click', async () => {
    useAuthStore.setState({ token: 'tok', username: 'admin', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    renderApp('/dashboard')
    await userEvent.click(screen.getByRole('button', { name: /sign out/i }))
    expect(useAuthStore.getState().token).toBeNull()
  })
})

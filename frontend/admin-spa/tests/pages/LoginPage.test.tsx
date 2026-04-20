import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MockAdapter from 'axios-mock-adapter'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from '../../src/pages/LoginPage'
import { apiClient } from '../../src/api/client'
import { useAuthStore } from '../../src/store/authStore'
import '../../src/i18n'

const mock = new MockAdapter(apiClient)

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  mock.reset()
  mockNavigate.mockReset()
  useAuthStore.setState({
    token: null,
    username: null,
    isAdmin: false,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

afterEach(() => {
  mock.reset()
})

describe('LoginPage — renders', () => {
  it('shows username and password fields', () => {
    renderLoginPage()
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('shows Sign In button', () => {
    renderLoginPage()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
})

describe('LoginPage — admin gate', () => {
  it('is_admin=true → login + navigate to /dashboard', async () => {
    mock.onPost('/v1/auth/token').reply(200, {
      access_token: 'jwt.tok',
      token_type: 'bearer',
      expires_in: 3600,
      is_admin: true,
    })
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'admin')
    await userEvent.type(screen.getByLabelText(/password/i), 'pass')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(useAuthStore.getState().token).toBe('jwt.tok')
      expect(useAuthStore.getState().isAdmin).toBe(true)
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('is_admin=false → shows access denied, no navigate', async () => {
    mock.onPost('/v1/auth/token').reply(200, {
      access_token: 'tok',
      token_type: 'bearer',
      expires_in: 3600,
      is_admin: false,
    })
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'user')
    await userEvent.type(screen.getByLabelText(/password/i), 'pass')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/access denied/i),
    )
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})

describe('LoginPage — error handling', () => {
  it('shows error_invalid on 401', async () => {
    mock.onPost('/v1/auth/token').reply(401)
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'bad')
    await userEvent.type(screen.getByLabelText(/password/i), 'bad')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i),
    )
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows error_unavailable on 500', async () => {
    mock.onPost('/v1/auth/token').reply(500)
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'u')
    await userEvent.type(screen.getByLabelText(/password/i), 'p')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/service unavailable/i),
    )
  })
})

describe('LoginPage — session expired banner', () => {
  it('shows session expired message when set in store', () => {
    useAuthStore.setState({
      token: null,
      username: null,
      isAdmin: false,
      sessionExpiredMessage: 'session_expired',
      _refreshTimer: null,
    })
    renderLoginPage()
    expect(screen.getByRole('alert')).toHaveTextContent(/session expired/i)
  })
})

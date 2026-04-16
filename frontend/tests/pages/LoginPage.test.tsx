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
  useAuthStore.setState({ token: null, username: null, password: null, _refreshTimer: null })
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

describe('LoginPage — success flow', () => {
  it('calls authStore.login and navigates to /query on 200', async () => {
    mock.onPost('/v1/auth/token').reply(200, {
      access_token: 'jwt.tok.en',
      token_type: 'bearer',
      expires_in: 3600,
    })
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'alice')
    await userEvent.type(screen.getByLabelText(/password/i), 'secret')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(useAuthStore.getState().token).toBe('jwt.tok.en')
      expect(mockNavigate).toHaveBeenCalledWith('/query')
    })
  })
})

describe('LoginPage — error handling', () => {
  it('shows error_invalid on 401', async () => {
    mock.onPost('/v1/auth/token').reply(401)
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'alice')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid username or password')
    })
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows error_unavailable on network error', async () => {
    mock.onPost('/v1/auth/token').networkError()
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'alice')
    await userEvent.type(screen.getByLabelText(/password/i), 'pw')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Service unavailable')
    })
  })

  it('disables submit button while loading', async () => {
    let resolveReq!: (value: unknown) => void
    mock.onPost('/v1/auth/token').reply(() => new Promise((res) => { resolveReq = res }))
    renderLoginPage()
    await userEvent.type(screen.getByLabelText(/username/i), 'alice')
    await userEvent.type(screen.getByLabelText(/password/i), 'pw')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled()
    resolveReq([200, { access_token: 'tok', token_type: 'bearer', expires_in: 3600 }])
  })
})

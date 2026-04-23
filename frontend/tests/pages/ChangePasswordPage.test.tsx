// Spec: docs/change-password/spec/change-password.spec.md#S005
// Task: S005/T004 — ChangePasswordPage tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ChangePasswordPage } from '../../src/pages/ChangePasswordPage'
import { useAuthStore } from '../../src/store/authStore'

const mockPatch = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../../src/api/client', () => ({
  apiClient: { patch: (...args: unknown[]) => mockPatch(...args) },
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'auth.force_change.title': 'You Must Change Your Password',
        'auth.force_change.notice': 'An administrator set your initial password.',
        'auth.force_change.new_password': 'New Password',
        'auth.force_change.confirm_password': 'Confirm New Password',
        'auth.force_change.submit': 'Set New Password',
        'auth.force_change.success': 'Password updated. Welcome!',
        'auth.force_change.error.mismatch': 'Passwords do not match.',
        'auth.force_change.error.too_short': 'Password must be at least 8 characters.',
        'results.error_service': 'Service error. Please try again.',
      }
      return map[key] ?? key
    },
  }),
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <ChangePasswordPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  mockPatch.mockReset()
  mockNavigate.mockReset()
  useAuthStore.setState({
    token: 'tok',
    username: 'alice',
    password: 'AdminSet123!',
    mustChangePassword: true,
    _refreshTimer: null,
  })
})

describe('ChangePasswordPage — render', () => {
  it('renders new password and confirm fields but NOT a current-password field', () => {
    renderPage()
    expect(screen.getByLabelText(/^new password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/current password/i)).not.toBeInTheDocument()
  })

  it('renders submit button', () => {
    renderPage()
    expect(screen.getByRole('button', { name: /set new password/i })).toBeInTheDocument()
  })
})

describe('ChangePasswordPage — client validation', () => {
  it('shows too_short error without calling API', async () => {
    renderPage()
    fireEvent.change(screen.getByLabelText(/^new password/i), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument()
    expect(mockPatch).not.toHaveBeenCalled()
  })

  it('shows mismatch error without calling API', async () => {
    renderPage()
    fireEvent.change(screen.getByLabelText(/^new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'Different1!' } })
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByText(/do not match/i)).toBeInTheDocument()
    expect(mockPatch).not.toHaveBeenCalled()
  })
})

describe('ChangePasswordPage — submit success', () => {
  it('calls PATCH with authStore.password as current_password, clears flag, navigates to /', async () => {
    mockPatch.mockResolvedValueOnce({ status: 204 })
    renderPage()

    fireEvent.change(screen.getByLabelText(/^new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }))

    await waitFor(() => {
      expect(mockPatch).toHaveBeenCalledWith('/v1/users/me/password', {
        current_password: 'AdminSet123!',
        new_password: 'NewPass123!',
      })
      expect(useAuthStore.getState().mustChangePassword).toBe(false)
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})

describe('ChangePasswordPage — API error', () => {
  it('shows service error on API failure', async () => {
    mockPatch.mockRejectedValueOnce(new Error('network'))
    renderPage()

    fireEvent.change(screen.getByLabelText(/^new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.change(screen.getByLabelText(/confirm new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Service error')
    expect(useAuthStore.getState().mustChangePassword).toBe(true)
  })
})

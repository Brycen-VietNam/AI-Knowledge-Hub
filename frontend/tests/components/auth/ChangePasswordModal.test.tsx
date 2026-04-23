// Spec: docs/change-password/spec/change-password.spec.md#S003
// Task: S003/T003 — ChangePasswordModal tests
// Rule: D6 — no inline styles; all CSS in index.css
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChangePasswordModal } from '../../../src/components/auth/ChangePasswordModal'

// Mock apiClient
const mockPatch = vi.fn()

vi.mock('../../../src/api/client', () => ({
  apiClient: { patch: (...args: unknown[]) => mockPatch(...args) },
}))

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'auth.change_password.title': 'Change Password',
        'auth.change_password.current_password': 'Current Password',
        'auth.change_password.new_password': 'New Password',
        'auth.change_password.confirm_password': 'Confirm Password',
        'auth.change_password.submit': 'Update Password',
        'auth.change_password.cancel': 'Cancel',
        'auth.change_password.success': 'Password updated successfully.',
        'auth.change_password.error.wrong_password': 'Current password is incorrect.',
        'auth.change_password.error.mismatch': 'New passwords do not match.',
        'auth.change_password.error.too_short': 'Password must be at least 8 characters.',
        'results.error_service': 'Service error. Please try again.',
      }
      return map[key] ?? key
    },
  }),
}))

function renderModal(onClose = vi.fn()) {
  return render(<ChangePasswordModal onClose={onClose} />)
}

describe('ChangePasswordModal — render', () => {
  it('renders all three password fields and action buttons', () => {
    renderModal()
    expect(screen.getByLabelText(/current password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /update password/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('calls onClose when Cancel is clicked', () => {
    const onClose = vi.fn()
    renderModal(onClose)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })
})

describe('ChangePasswordModal — client validation', () => {
  beforeEach(() => { mockPatch.mockReset() })

  it('shows too_short error when new password < 8 chars (no API call)', async () => {
    renderModal()
    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: 'OldPass1!' } })
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument()
    expect(mockPatch).not.toHaveBeenCalled()
  })

  it('shows mismatch error when new ≠ confirm (no API call)', async () => {
    renderModal()
    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: 'OldPass1!' } })
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'Different1!' } })
    fireEvent.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText(/do not match/i)).toBeInTheDocument()
    expect(mockPatch).not.toHaveBeenCalled()
  })
})

describe('ChangePasswordModal — submit success', () => {
  beforeEach(() => { mockPatch.mockReset() })

  it('calls PATCH /v1/users/me/password and shows success message', async () => {
    mockPatch.mockResolvedValueOnce({ status: 204 })
    renderModal()

    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: 'OldPass1!' } })
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'NewPass123!' } })
    fireEvent.click(screen.getByRole('button', { name: /update password/i }))

    await waitFor(() => {
      expect(mockPatch).toHaveBeenCalledWith('/v1/users/me/password', {
        current_password: 'OldPass1!',
        new_password: 'NewPass123!',
      })
    })
    expect(await screen.findByText(/password updated successfully/i)).toBeInTheDocument()
  })
})

describe('ChangePasswordModal — ERR_WRONG_PASSWORD', () => {
  beforeEach(() => { mockPatch.mockReset() })

  it('shows inline field error on ERR_WRONG_PASSWORD (401)', async () => {
    mockPatch.mockRejectedValueOnce({
      response: { data: { error: { code: 'ERR_WRONG_PASSWORD' } } },
    })
    renderModal()

    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: 'WrongPass1!' } })
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'NewPass123!' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'NewPass123!' } })
    fireEvent.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText(/current password is incorrect/i)).toBeInTheDocument()
  })
})

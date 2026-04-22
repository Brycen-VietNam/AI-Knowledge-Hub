// Spec: docs/change-password/spec/change-password.spec.md#S004
// Task: S004/T003 — ResetPasswordModal tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ResetPasswordModal } from '../../../src/components/admin/ResetPasswordModal'

const mockPost = vi.fn()

vi.mock('../../../src/api/client', () => ({
  apiClient: { post: (...args: unknown[]) => mockPost(...args) },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'auth.reset_password.title': 'Reset User Password',
        'auth.reset_password.option_manual': 'Set password manually',
        'auth.reset_password.option_generate': 'Auto-generate password',
        'auth.reset_password.new_password': 'New Password',
        'auth.reset_password.generated_label': 'Generated Password',
        'auth.reset_password.copy': 'Copy',
        'auth.reset_password.warning': 'This password will only be shown once.',
        'auth.reset_password.submit': 'Reset Password',
        'auth.reset_password.cancel': 'Cancel',
        'auth.reset_password.success': 'Password has been reset successfully.',
        'auth.reset_password.error.too_short': 'Password must be at least 8 characters.',
        'auth.reset_password.error.oidc_not_applicable': 'This user authenticates via SSO.',
        'results.error_service': 'Service error. Please try again.',
      }
      return map[key] ?? key
    },
  }),
}))

function renderModal(userId = 'user-1', onClose = vi.fn()) {
  return render(<ResetPasswordModal userId={userId} onClose={onClose} />)
}

describe('ResetPasswordModal — render', () => {
  it('renders title and both mode radio buttons', () => {
    renderModal()
    expect(screen.getByText(/reset user password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/auto-generate password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/set password manually/i)).toBeInTheDocument()
  })

  it('calls onClose when Cancel is clicked', () => {
    const onClose = vi.fn()
    renderModal('u1', onClose)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('does not show New Password field in generate mode (default)', () => {
    renderModal()
    expect(screen.queryByLabelText(/new password/i)).not.toBeInTheDocument()
  })

  it('shows New Password field when manual mode selected', () => {
    renderModal()
    fireEvent.click(screen.getByLabelText(/set password manually/i))
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
  })
})

describe('ResetPasswordModal — generate mode', () => {
  beforeEach(() => { mockPost.mockReset() })

  it('calls POST with {generate:true} and shows generated password', async () => {
    mockPost.mockResolvedValueOnce({ data: { password: 'Abc123!@#' } })
    renderModal('user-42')

    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/v1/admin/users/user-42/password-reset',
        { generate: true },
      )
    })
    expect(await screen.findByDisplayValue('Abc123!@#')).toBeInTheDocument()
    expect(screen.getByText(/this password will only be shown once/i)).toBeInTheDocument()
  })
})

describe('ResetPasswordModal — manual mode', () => {
  beforeEach(() => { mockPost.mockReset() })

  it('shows too_short error when password < 8 chars (no API call)', async () => {
    renderModal()
    fireEvent.click(screen.getByLabelText(/set password manually/i))
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument()
    expect(mockPost).not.toHaveBeenCalled()
  })

  it('calls POST with {new_password} on valid manual input and shows success', async () => {
    mockPost.mockResolvedValueOnce({ status: 204 })
    renderModal('user-7')

    fireEvent.click(screen.getByLabelText(/set password manually/i))
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'SecurePass1!' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/v1/admin/users/user-7/password-reset',
        { new_password: 'SecurePass1!' },
      )
    })
    expect(await screen.findByText(/password has been reset successfully/i)).toBeInTheDocument()
  })
})

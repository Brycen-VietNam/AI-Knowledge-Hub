// Spec: docs/change-password/spec/change-password.spec.md#S004
// Task: S004/T004 — UsersTab: Reset Password button visibility + modal render
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { UsersTab, AdminUser } from '../../../src/components/admin/UsersTab'

// Stub ResetPasswordModal so UsersTab tests stay isolated
vi.mock('../../../src/components/admin/ResetPasswordModal', () => ({
  ResetPasswordModal: ({ userId, onClose }: { userId: string; onClose: () => void }) => (
    <div data-testid="reset-modal" data-user-id={userId}>
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))

const passwordUser: AdminUser = {
  id: 'u1',
  username: 'alice',
  email: 'alice@example.com',
  role: 'user',
  has_password: true,
}

const oidcUser: AdminUser = {
  id: 'u2',
  username: 'bob',
  email: 'bob@example.com',
  role: 'user',
  has_password: false,
}

describe('UsersTab — Reset Password button visibility', () => {
  it('shows Reset Password button for password-based user', () => {
    render(<UsersTab users={[passwordUser]} />)
    expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument()
  })

  it('hides Reset Password button for OIDC user (has_password=false)', () => {
    render(<UsersTab users={[oidcUser]} />)
    expect(screen.queryByRole('button', { name: /reset password/i })).not.toBeInTheDocument()
  })

  it('renders one Reset Password button per password-based user row', () => {
    render(<UsersTab users={[passwordUser, oidcUser]} />)
    expect(screen.getAllByRole('button', { name: /reset password/i })).toHaveLength(1)
  })
})

describe('UsersTab — modal open/close', () => {
  it('opens ResetPasswordModal with correct userId on button click', () => {
    render(<UsersTab users={[passwordUser]} />)
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    const modal = screen.getByTestId('reset-modal')
    expect(modal).toBeInTheDocument()
    expect(modal).toHaveAttribute('data-user-id', 'u1')
  })

  it('closes modal when onClose is called', () => {
    render(<UsersTab users={[passwordUser]} />)
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    expect(screen.getByTestId('reset-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(screen.queryByTestId('reset-modal')).not.toBeInTheDocument()
  })
})

// Spec: docs/change-password/spec/change-password.spec.md#S004
// Task: S004/T004 — UsersTab admin table with Reset Password button
// Rule: D6 — all CSS in index.css; no inline styles, no CSS modules, no Tailwind
// Decision: D3 — Reset Password button hidden for OIDC users (has_password=false)
import { useState } from 'react'
import { ResetPasswordModal } from './ResetPasswordModal'

export interface AdminUser {
  id: string
  username: string
  email: string
  role: string
  has_password: boolean
}

interface Props {
  users: AdminUser[]
}

export function UsersTab({ users }: Props) {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)

  return (
    <div className="users-tab">
      <table className="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                {user.has_password && (
                  <button
                    className="btn-reset-password"
                    onClick={() => setSelectedUserId(user.id)}
                  >
                    Reset Password
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedUserId && (
        <ResetPasswordModal
          userId={selectedUserId}
          onClose={() => setSelectedUserId(null)}
        />
      )}
    </div>
  )
}

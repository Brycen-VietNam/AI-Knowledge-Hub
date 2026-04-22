// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T005 — ProtectedRoute — redirect to /login if no token
// Task: S005/T005 — redirect to /change-password if mustChangePassword (not already there)
import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

interface Props {
  children: ReactNode
}

export function ProtectedRoute({ children }: Props) {
  const token = useAuthStore((s) => s.token)
  const mustChangePassword = useAuthStore((s) => s.mustChangePassword)
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" replace />
  }
  if (mustChangePassword && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }
  return <>{children}</>
}

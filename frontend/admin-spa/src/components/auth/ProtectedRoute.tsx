// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T006 — ProtectedRoute — redirect to /login if no token OR !isAdmin (AC7, AC8)
import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

interface Props {
  children: ReactNode
}

export function ProtectedRoute({ children }: Props) {
  const { token, isAdmin } = useAuthStore()
  if (!token || !isAdmin) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

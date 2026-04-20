// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T006 — useAdminGuard — imperative hook, redirects on mount if not admin
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function useAdminGuard() {
  const { token, isAdmin } = useAuthStore()
  const navigate = useNavigate()
  useEffect(() => {
    if (!token || !isAdmin) {
      navigate('/login', { replace: true })
    }
  }, [token, isAdmin, navigate])
}

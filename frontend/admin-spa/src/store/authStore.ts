// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T002 — authStore (Zustand) — token + isAdmin + sessionExpiredMessage + login/logout
// Decision: isAdmin default false; login receives isAdmin from API response (not self-computed)
import { create } from 'zustand'

interface AuthState {
  token: string | null
  username: string | null
  isAdmin: boolean
  sessionExpiredMessage: string | null
  _refreshTimer: ReturnType<typeof setTimeout> | null
  login: (token: string, username: string, isAdmin: boolean) => void
  logout: () => void
  setSessionExpired: () => void
  clearSessionExpired: () => void
  scheduleRefresh: (expSeconds: number, refreshFn: () => void) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  username: null,
  isAdmin: false,
  sessionExpiredMessage: null,
  _refreshTimer: null,

  login: (token, username, isAdmin) => {
    set({ token, username, isAdmin, sessionExpiredMessage: null })
  },

  logout: () => {
    const { _refreshTimer } = get()
    if (_refreshTimer !== null) {
      clearTimeout(_refreshTimer)
    }
    set({ token: null, username: null, isAdmin: false, _refreshTimer: null })
  },

  setSessionExpired: () => {
    set({ sessionExpiredMessage: 'session_expired' })
  },

  clearSessionExpired: () => {
    set({ sessionExpiredMessage: null })
  },

  scheduleRefresh: (expSeconds, refreshFn) => {
    const { _refreshTimer } = get()
    if (_refreshTimer !== null) {
      clearTimeout(_refreshTimer)
    }
    const msUntilRefresh = (expSeconds - Date.now() / 1000 - 300) * 1000
    if (msUntilRefresh <= 0) {
      refreshFn()
      return
    }
    const timer = setTimeout(refreshFn, msUntilRefresh)
    set({ _refreshTimer: timer })
  },
}))

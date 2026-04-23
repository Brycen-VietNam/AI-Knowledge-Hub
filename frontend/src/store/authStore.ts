// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T002 — authStore (Zustand) — token + login/logout + proactive refresh
// Task: T005 (S004) — clearHistory on logout (D004)
// Decision: D002 — token in memory ONLY (no localStorage); D011 — refresh 5min before exp
import { create } from 'zustand'
import { useQueryStore } from './queryStore'

interface AuthState {
  token: string | null
  username: string | null
  password: string | null
  mustChangePassword: boolean
  _refreshTimer: ReturnType<typeof setTimeout> | null
  login: (token: string, username: string, password: string, mustChangePassword?: boolean) => void
  logout: () => void
  clearMustChangePassword: () => void
  scheduleRefresh: (expSeconds: number, refreshFn: () => void) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  username: null,
  password: null,
  mustChangePassword: false,
  _refreshTimer: null,

  login: (token, username, password, mustChangePassword = false) => {
    set({ token, username, password, mustChangePassword })
  },

  logout: () => {
    useQueryStore.getState().clearHistory()
    const { _refreshTimer } = get()
    if (_refreshTimer !== null) {
      clearTimeout(_refreshTimer)
    }
    set({ token: null, username: null, password: null, mustChangePassword: false, _refreshTimer: null })
  },

  clearMustChangePassword: () => {
    set({ mustChangePassword: false })
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

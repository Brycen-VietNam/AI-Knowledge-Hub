// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Spec: docs/security-audit/spec/security-audit.spec.md#S001
// Task: T002 — authStore (Zustand) — token + login/logout + proactive refresh
// Task: T005 (S004) — clearHistory on logout (D004)
// Task: S001/T005 — remove password, add refreshToken, add refreshAccessToken (D-SA-02)
// Decision: D002 — token in memory ONLY (no localStorage); D011 — refresh 5min before exp
// Decision: D-SA-02 — refreshToken in memory only (not localStorage — XSS boundary)
import { create } from 'zustand'
import { apiClient } from '../api/client'
import { useQueryStore } from './queryStore'

interface TokenRefreshResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

interface AuthState {
  token: string | null
  refreshToken: string | null
  username: string | null
  mustChangePassword: boolean
  _refreshTimer: ReturnType<typeof setTimeout> | null
  login: (accessToken: string, refreshToken: string, username: string, mustChangePassword?: boolean) => void
  logout: () => void
  clearMustChangePassword: () => void
  scheduleRefresh: (expSeconds: number, refreshFn: () => void) => void
  refreshAccessToken: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  refreshToken: null,
  username: null,
  mustChangePassword: false,
  _refreshTimer: null,

  login: (accessToken, refreshToken, username, mustChangePassword = false) => {
    set({ token: accessToken, refreshToken, username, mustChangePassword })
  },

  logout: () => {
    useQueryStore.getState().clearHistory()
    const { _refreshTimer } = get()
    if (_refreshTimer !== null) {
      clearTimeout(_refreshTimer)
    }
    set({ token: null, refreshToken: null, username: null, mustChangePassword: false, _refreshTimer: null })
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

  refreshAccessToken: async () => {
    const { refreshToken, username, mustChangePassword } = get()
    if (!refreshToken) {
      get().logout()
      return
    }
    try {
      const { data } = await apiClient.post<TokenRefreshResponse>('/v1/auth/refresh', {
        refresh_token: refreshToken,
      })
      get().login(data.access_token, data.refresh_token, username ?? '', mustChangePassword)
      const nextExp = Date.now() / 1000 + data.expires_in
      get().scheduleRefresh(nextExp, () => get().refreshAccessToken())
    } catch {
      get().logout()
    }
  },
}))

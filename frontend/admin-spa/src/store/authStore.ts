// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T002 — authStore (Zustand) — token + isAdmin + sessionExpiredMessage + login/logout
// Decision: isAdmin default false; login receives isAdmin from API response (not self-computed)
// Decision: sessionStorage persist — survives SPA navigation and page refresh within same tab;
//           clears on tab close (safer than localStorage, better UX than pure in-memory)
import { create } from 'zustand'

const SS_KEY = 'kh_admin_auth'

function loadFromSession(): { token: string | null; username: string | null; isAdmin: boolean } {
  try {
    const raw = sessionStorage.getItem(SS_KEY)
    if (!raw) return { token: null, username: null, isAdmin: false }
    const parsed = JSON.parse(raw)
    return {
      token: typeof parsed.token === 'string' ? parsed.token : null,
      username: typeof parsed.username === 'string' ? parsed.username : null,
      isAdmin: parsed.isAdmin === true,
    }
  } catch {
    return { token: null, username: null, isAdmin: false }
  }
}

function saveToSession(token: string, username: string, isAdmin: boolean) {
  try {
    sessionStorage.setItem(SS_KEY, JSON.stringify({ token, username, isAdmin }))
  } catch {
    // sessionStorage unavailable — silently continue
  }
}

function clearSession() {
  try {
    sessionStorage.removeItem(SS_KEY)
  } catch { /* ignore */ }
}

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

const _session = loadFromSession()

export const useAuthStore = create<AuthState>((set, get) => ({
  token: _session.token,
  username: _session.username,
  isAdmin: _session.isAdmin,
  sessionExpiredMessage: null,
  _refreshTimer: null,

  login: (token, username, isAdmin) => {
    saveToSession(token, username, isAdmin)
    set({ token, username, isAdmin, sessionExpiredMessage: null })
  },

  logout: () => {
    const { _refreshTimer } = get()
    if (_refreshTimer !== null) {
      clearTimeout(_refreshTimer)
    }
    clearSession()
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

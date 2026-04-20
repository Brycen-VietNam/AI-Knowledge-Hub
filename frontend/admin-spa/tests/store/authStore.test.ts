import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useAuthStore } from '../../src/store/authStore'

beforeEach(() => {
  useAuthStore.setState({
    token: null,
    username: null,
    isAdmin: false,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

afterEach(() => {
  vi.clearAllTimers()
})

describe('authStore — login', () => {
  it('sets token, username, isAdmin=true', () => {
    useAuthStore.getState().login('tok1', 'alice', true)
    const { token, username, isAdmin } = useAuthStore.getState()
    expect(token).toBe('tok1')
    expect(username).toBe('alice')
    expect(isAdmin).toBe(true)
  })

  it('sets isAdmin=false when false passed', () => {
    useAuthStore.getState().login('tok2', 'bob', false)
    expect(useAuthStore.getState().isAdmin).toBe(false)
  })

  it('clears sessionExpiredMessage on login', () => {
    useAuthStore.getState().setSessionExpired()
    useAuthStore.getState().login('tok', 'u', true)
    expect(useAuthStore.getState().sessionExpiredMessage).toBeNull()
  })
})

describe('authStore — logout', () => {
  it('clears token, username, isAdmin', () => {
    useAuthStore.getState().login('tok1', 'alice', true)
    useAuthStore.getState().logout()
    const { token, username, isAdmin } = useAuthStore.getState()
    expect(token).toBeNull()
    expect(username).toBeNull()
    expect(isAdmin).toBe(false)
  })
})

describe('authStore — defaults', () => {
  it('isAdmin defaults to false', () => {
    expect(useAuthStore.getState().isAdmin).toBe(false)
  })
})

describe('authStore — sessionExpired', () => {
  it('setSessionExpired sets message', () => {
    useAuthStore.getState().setSessionExpired()
    expect(useAuthStore.getState().sessionExpiredMessage).toBe('session_expired')
  })

  it('clearSessionExpired clears message', () => {
    useAuthStore.getState().setSessionExpired()
    useAuthStore.getState().clearSessionExpired()
    expect(useAuthStore.getState().sessionExpiredMessage).toBeNull()
  })
})

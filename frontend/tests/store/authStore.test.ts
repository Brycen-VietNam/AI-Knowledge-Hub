import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore } from '../../src/store/authStore'
import { useQueryStore } from '../../src/store/queryStore'

beforeEach(() => {
  useAuthStore.setState({
    token: null,
    username: null,
    password: null,
    _refreshTimer: null,
  })
  useQueryStore.setState({ history: [] })
})

describe('authStore — login', () => {
  it('sets token, username, password', () => {
    useAuthStore.getState().login('tok123', 'alice', 'pw')
    const { token, username, password } = useAuthStore.getState()
    expect(token).toBe('tok123')
    expect(username).toBe('alice')
    expect(password).toBe('pw')
  })
})

describe('authStore — logout', () => {
  it('clears token, username, password', () => {
    useAuthStore.getState().login('tok123', 'alice', 'pw')
    useAuthStore.getState().logout()
    const { token, username, password } = useAuthStore.getState()
    expect(token).toBeNull()
    expect(username).toBeNull()
    expect(password).toBeNull()
  })

  it('cancels pending refresh timer', () => {
    const clearSpy = vi.spyOn(globalThis, 'clearTimeout')
    // Set a fake timer id
    useAuthStore.setState({ _refreshTimer: 999 as unknown as ReturnType<typeof setTimeout> })
    useAuthStore.getState().logout()
    expect(clearSpy).toHaveBeenCalledWith(999)
    clearSpy.mockRestore()
  })

  it('token is never in localStorage', () => {
    useAuthStore.getState().login('tok123', 'alice', 'pw')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('clears queryStore history on logout', () => {
    useQueryStore.getState().addHistory('q1', 'a1', [])
    expect(useQueryStore.getState().history).toHaveLength(1)
    useAuthStore.getState().logout()
    expect(useQueryStore.getState().history).toHaveLength(0)
  })
})

describe('authStore — scheduleRefresh', () => {
  it('fires callback before exp', () => {
    vi.useFakeTimers()
    const refreshFn = vi.fn()
    // exp = 10 minutes from now → fires in 5 minutes (300s before)
    const expSeconds = Date.now() / 1000 + 600
    useAuthStore.getState().scheduleRefresh(expSeconds, refreshFn)
    vi.advanceTimersByTime(300_001)
    expect(refreshFn).toHaveBeenCalledTimes(1)
    vi.useRealTimers()
  })

  it('clears prior timer before setting new one', () => {
    vi.useFakeTimers()
    const clearSpy = vi.spyOn(globalThis, 'clearTimeout')
    const fakeTimer = 777 as unknown as ReturnType<typeof setTimeout>
    useAuthStore.setState({ _refreshTimer: fakeTimer })
    const expSeconds = Date.now() / 1000 + 600
    useAuthStore.getState().scheduleRefresh(expSeconds, vi.fn())
    expect(clearSpy).toHaveBeenCalledWith(fakeTimer)
    clearSpy.mockRestore()
    vi.useRealTimers()
  })

  it('fires immediately if exp is already past refresh window', () => {
    const refreshFn = vi.fn()
    const expSeconds = Date.now() / 1000 + 100 // only 100s left, < 300s buffer
    useAuthStore.getState().scheduleRefresh(expSeconds, refreshFn)
    expect(refreshFn).toHaveBeenCalledTimes(1)
  })
})

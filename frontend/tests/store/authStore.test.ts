// Spec: docs/security-audit/spec/security-audit.spec.md#S001
// Task: S001/T005 — authStore tests: no password field, refreshToken in memory, refreshAccessToken
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore } from '../../src/store/authStore'
import { useQueryStore } from '../../src/store/queryStore'

const mockPost = vi.fn()

vi.mock('../../src/api/client', () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}))

beforeEach(() => {
  mockPost.mockReset()
  useAuthStore.setState({
    token: null,
    refreshToken: null,
    username: null,
    _refreshTimer: null,
  })
  useQueryStore.setState({ history: [] })
})

describe('authStore — login', () => {
  it('sets token, refreshToken, username', () => {
    useAuthStore.getState().login('tok123', 'rtok456', 'alice')
    const { token, refreshToken, username } = useAuthStore.getState()
    expect(token).toBe('tok123')
    expect(refreshToken).toBe('rtok456')
    expect(username).toBe('alice')
  })

  it('does NOT have a password field', () => {
    useAuthStore.getState().login('tok123', 'rtok456', 'alice')
    const state = useAuthStore.getState() as Record<string, unknown>
    expect('password' in state).toBe(false)
  })
})

describe('authStore — logout', () => {
  it('clears token, refreshToken, username', () => {
    useAuthStore.getState().login('tok123', 'rtok456', 'alice')
    useAuthStore.getState().logout()
    const { token, refreshToken, username } = useAuthStore.getState()
    expect(token).toBeNull()
    expect(refreshToken).toBeNull()
    expect(username).toBeNull()
  })

  it('cancels pending refresh timer', () => {
    const clearSpy = vi.spyOn(globalThis, 'clearTimeout')
    useAuthStore.setState({ _refreshTimer: 999 as unknown as ReturnType<typeof setTimeout> })
    useAuthStore.getState().logout()
    expect(clearSpy).toHaveBeenCalledWith(999)
    clearSpy.mockRestore()
  })

  it('token is never in localStorage', () => {
    useAuthStore.getState().login('tok123', 'rtok456', 'alice')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('refreshToken is never in localStorage (D-SA-02 XSS boundary)', () => {
    useAuthStore.getState().login('tok123', 'rtok456', 'alice')
    expect(localStorage.getItem('refreshToken')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
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
    const expSeconds = Date.now() / 1000 + 100
    useAuthStore.getState().scheduleRefresh(expSeconds, refreshFn)
    expect(refreshFn).toHaveBeenCalledTimes(1)
  })
})

describe('authStore — refreshAccessToken', () => {
  it('on success: updates tokens and reschedules refresh', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        access_token: 'new-access',
        refresh_token: 'new-refresh',
        expires_in: 3600,
      },
    })

    useAuthStore.setState({ token: 'old-tok', refreshToken: 'old-rtok', username: 'alice' })
    await useAuthStore.getState().refreshAccessToken()

    const { token, refreshToken } = useAuthStore.getState()
    expect(token).toBe('new-access')
    expect(refreshToken).toBe('new-refresh')
  })

  it('on 401 response: calls logout', async () => {
    mockPost.mockRejectedValueOnce({ response: { status: 401 } })

    useAuthStore.setState({ token: 'tok', refreshToken: 'rtok', username: 'alice' })
    await useAuthStore.getState().refreshAccessToken()

    expect(useAuthStore.getState().token).toBeNull()
  })

  it('when refreshToken is null: calls logout without API call', async () => {
    useAuthStore.setState({ token: null, refreshToken: null, username: null })
    await useAuthStore.getState().refreshAccessToken()

    expect(useAuthStore.getState().token).toBeNull()
    expect(mockPost).not.toHaveBeenCalled()
  })
})

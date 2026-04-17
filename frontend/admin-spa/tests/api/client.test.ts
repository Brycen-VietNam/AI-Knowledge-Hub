import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { apiClient, setNavigate } from '../../src/api/client'
import { useAuthStore } from '../../src/store/authStore'

const mock = new MockAdapter(apiClient)

beforeEach(() => {
  mock.reset()
  setNavigate(null as unknown as (path: string) => void)
  useAuthStore.setState({
    token: null,
    username: null,
    isAdmin: false,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

afterEach(() => {
  mock.reset()
})

describe('apiClient — request interceptor', () => {
  it('attaches Bearer token when logged in', async () => {
    useAuthStore.setState({ token: 'mytoken', username: 'u', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    mock.onGet('/v1/health').reply(200, {})
    await apiClient.get('/v1/health')
    const sentHeaders = mock.history.get[0].headers as Record<string, string>
    expect(sentHeaders['Authorization']).toBe('Bearer mytoken')
  })

  it('omits Authorization header when not logged in', async () => {
    mock.onGet('/v1/health').reply(200, {})
    await apiClient.get('/v1/health')
    const sentHeaders = mock.history.get[0].headers as Record<string, string>
    expect(sentHeaders['Authorization']).toBeUndefined()
  })
})

describe('apiClient — response interceptor', () => {
  it('401 triggers logout + navigate + setSessionExpired', async () => {
    useAuthStore.setState({ token: 'tok', username: 'u', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    const navigateMock = vi.fn()
    setNavigate(navigateMock)
    mock.onGet('/v1/protected').reply(401)

    await expect(apiClient.get('/v1/protected')).rejects.toThrow()

    expect(useAuthStore.getState().token).toBeNull()
    expect(useAuthStore.getState().sessionExpiredMessage).toBe('session_expired')
    expect(navigateMock).toHaveBeenCalledWith('/login')
  })

  it('non-401 error does not trigger logout', async () => {
    useAuthStore.setState({ token: 'tok', username: 'u', isAdmin: true, sessionExpiredMessage: null, _refreshTimer: null })
    mock.onGet('/v1/test').reply(500)

    await expect(apiClient.get('/v1/test')).rejects.toThrow()

    expect(useAuthStore.getState().token).toBe('tok')
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { apiClient, setNavigate } from '../../src/api/client'
import { useAuthStore } from '../../src/store/authStore'

const mock = new MockAdapter(apiClient)

beforeEach(() => {
  mock.reset()
  useAuthStore.setState({
    token: null,
    username: null,
    password: null,
    _refreshTimer: null,
  })
})

afterEach(() => {
  mock.reset()
})

describe('apiClient — request interceptor', () => {
  it('attaches Bearer token when logged in', async () => {
    useAuthStore.setState({ token: 'mytoken' })
    mock.onGet('/v1/health').reply(200, {})
    const res = await apiClient.get('/v1/health')
    const sentHeaders = mock.history.get[0].headers as Record<string, string>
    expect(sentHeaders['Authorization']).toBe('Bearer mytoken')
    expect(res.status).toBe(200)
  })

  it('omits Authorization header when not logged in', async () => {
    mock.onGet('/v1/health').reply(200, {})
    await apiClient.get('/v1/health')
    const sentHeaders = mock.history.get[0].headers as Record<string, string>
    expect(sentHeaders['Authorization']).toBeUndefined()
  })
})

describe('apiClient — response interceptor', () => {
  it('calls logout + navigate on 401', async () => {
    useAuthStore.setState({ token: 'oldtok', username: 'u', password: 'p' })
    const navigateMock = vi.fn()
    setNavigate(navigateMock)
    mock.onGet('/v1/query').reply(401)

    await expect(apiClient.get('/v1/query')).rejects.toThrow()

    expect(useAuthStore.getState().token).toBeNull()
    expect(navigateMock).toHaveBeenCalledWith('/login')

    setNavigate(() => {}) // reset
  })

  it('re-throws non-401 errors', async () => {
    mock.onGet('/v1/query').reply(500, { error: { code: 'SERVER_ERROR' } })
    await expect(apiClient.get('/v1/query')).rejects.toMatchObject({
      response: { status: 500 },
    })
    // token should NOT be cleared on 500
    useAuthStore.setState({ token: 'alive' })
    mock.onGet('/v1/query').reply(500)
    await expect(apiClient.get('/v1/query')).rejects.toBeDefined()
    expect(useAuthStore.getState().token).toBe('alive')
  })
})

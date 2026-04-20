// Task: T002 (S004) — metricsApi.ts tests
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { apiClient } from '../../src/api/client'
import { getMetrics, MetricsData } from '../../src/api/metricsApi'
import { useAuthStore } from '../../src/store/authStore'

const mock = new MockAdapter(apiClient)

const sampleMetrics: MetricsData = {
  documents: { total: 32, ready: 30, processing: 0, error: 2 },
  users: { total: 15, active: 10 },
  groups: { total: 5 },
  queries: { last_7_days: [{ date: '2026-04-14', count: 12 }] },
  health: { database: 'ok', api: 'ok' },
}

beforeEach(() => {
  mock.reset()
  useAuthStore.setState({
    token: 'test-token',
    username: 'admin',
    isAdmin: true,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
})

afterEach(() => {
  mock.reset()
})

describe('getMetrics', () => {
  it('calls GET /v1/metrics and returns MetricsData', async () => {
    mock.onGet('/v1/metrics').reply(200, sampleMetrics)
    const result = await getMetrics()
    expect(result).toEqual(sampleMetrics)
  })

  it('throws on 403', async () => {
    mock.onGet('/v1/metrics').reply(403, { error: { code: 'FORBIDDEN' } })
    await expect(getMetrics()).rejects.toThrow()
  })

  it('throws on network error', async () => {
    mock.onGet('/v1/metrics').networkError()
    await expect(getMetrics()).rejects.toThrow()
  })
})

import { describe, it, expect, beforeEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { apiClient } from '../../src/api/client'
import { useQueryStore } from '../../src/store/queryStore'

const mock = new MockAdapter(apiClient)

beforeEach(() => {
  mock.reset()
  useQueryStore.setState({ query: '', isLoading: false, error: null, result: null, history: [] })
})

describe('queryStore — initial state', () => {
  it('has empty query', () => {
    expect(useQueryStore.getState().query).toBe('')
  })

  it('isLoading is false', () => {
    expect(useQueryStore.getState().isLoading).toBe(false)
  })

  it('error is null', () => {
    expect(useQueryStore.getState().error).toBeNull()
  })
})

describe('queryStore — setQuery', () => {
  it('updates query string', () => {
    useQueryStore.getState().setQuery('what is RBAC?')
    expect(useQueryStore.getState().query).toBe('what is RBAC?')
  })
})

describe('queryStore — setLoading', () => {
  it('sets isLoading to true', () => {
    useQueryStore.getState().setLoading(true)
    expect(useQueryStore.getState().isLoading).toBe(true)
  })

  it('sets isLoading to false', () => {
    useQueryStore.getState().setLoading(true)
    useQueryStore.getState().setLoading(false)
    expect(useQueryStore.getState().isLoading).toBe(false)
  })
})

describe('queryStore — setError', () => {
  it('sets error message', () => {
    useQueryStore.getState().setError('network error')
    expect(useQueryStore.getState().error).toBe('network error')
  })

  it('clears error with null', () => {
    useQueryStore.getState().setError('network error')
    useQueryStore.getState().setError(null)
    expect(useQueryStore.getState().error).toBeNull()
  })
})

describe('queryStore — reset', () => {
  it('clears query, isLoading, and error', () => {
    useQueryStore.getState().setQuery('test query')
    useQueryStore.getState().setLoading(true)
    useQueryStore.getState().setError('some error')
    useQueryStore.getState().reset()
    const { query, isLoading, error } = useQueryStore.getState()
    expect(query).toBe('')
    expect(isLoading).toBe(false)
    expect(error).toBeNull()
  })
})

describe('queryStore — no localStorage', () => {
  it('query state never stored in localStorage', () => {
    useQueryStore.getState().setQuery('secret query')
    expect(localStorage.getItem('query')).toBeNull()
  })
})

describe('queryStore — submitQuery success', () => {
  it('sets result on 200 response', async () => {
    const payload = {
      answer: 'RBAC is role-based access control.',
      citations: [{ doc_id: 'd1', title: 'Doc 1', score: 0.91, chunk_preview: 'preview' }],
      confidence: 0.85,
    }
    mock.onPost('/v1/query').reply(200, payload)
    await useQueryStore.getState().submitQuery('what is RBAC?', 'en')
    const { result, isLoading, error } = useQueryStore.getState()
    expect(result).toEqual(payload)
    expect(isLoading).toBe(false)
    expect(error).toBeNull()
  })

  it('clears previous result and error on new submit', async () => {
    useQueryStore.setState({
      result: { answer: 'old', citations: [], confidence: 0.5 },
      error: 'old error',
    })
    mock.onPost('/v1/query').reply(200, { answer: 'new', citations: [], confidence: 0.9 })
    await useQueryStore.getState().submitQuery('new query', 'ja')
    const { result, error } = useQueryStore.getState()
    expect(result?.answer).toBe('new')
    expect(error).toBeNull()
  })

  it('isLoading is false after successful call (finally block)', async () => {
    mock.onPost('/v1/query').reply(200, { answer: 'ok', citations: [], confidence: 0.8 })
    await useQueryStore.getState().submitQuery('test', 'en')
    expect(useQueryStore.getState().isLoading).toBe(false)
  })
})

describe('queryStore — submitQuery errors', () => {
  it('sets rate-limit error on 429', async () => {
    mock.onPost('/v1/query').reply(429)
    await useQueryStore.getState().submitQuery('test', 'en')
    const { error, isLoading } = useQueryStore.getState()
    expect(error).toBe('results.error_rate_limit')
    expect(isLoading).toBe(false)
  })

  it('sets service error on 500', async () => {
    mock.onPost('/v1/query').reply(500)
    await useQueryStore.getState().submitQuery('test', 'en')
    expect(useQueryStore.getState().error).toBe('results.error_service')
  })

  it('sets service error on 503', async () => {
    mock.onPost('/v1/query').reply(503)
    await useQueryStore.getState().submitQuery('test', 'en')
    expect(useQueryStore.getState().error).toBe('results.error_service')
  })

  it('sets service error on network failure', async () => {
    mock.onPost('/v1/query').networkError()
    await useQueryStore.getState().submitQuery('test', 'en')
    expect(useQueryStore.getState().error).toBe('results.error_service')
  })

  it('isLoading is false after error (finally block)', async () => {
    mock.onPost('/v1/query').reply(500)
    await useQueryStore.getState().submitQuery('test', 'en')
    expect(useQueryStore.getState().isLoading).toBe(false)
  })

  it('result remains null on error', async () => {
    mock.onPost('/v1/query').reply(500)
    await useQueryStore.getState().submitQuery('test', 'en')
    expect(useQueryStore.getState().result).toBeNull()
  })
})

describe('queryStore — addHistory', () => {
  it('adds item to history (newest first)', () => {
    useQueryStore.getState().addHistory('q1', 'a1', [])
    useQueryStore.getState().addHistory('q2', 'a2', [])
    const { history } = useQueryStore.getState()
    expect(history[0].query).toBe('q2')
    expect(history[1].query).toBe('q1')
  })

  it('caps history at 20 items', () => {
    for (let i = 0; i < 25; i++) {
      useQueryStore.getState().addHistory(`q${i}`, `a${i}`, [])
    }
    expect(useQueryStore.getState().history).toHaveLength(20)
  })
})

describe('queryStore — clearHistory', () => {
  it('empties history array', () => {
    useQueryStore.getState().addHistory('q1', 'a1', [])
    useQueryStore.getState().clearHistory()
    expect(useQueryStore.getState().history).toHaveLength(0)
  })
})

describe('queryStore — selectHistory', () => {
  it('restores query and result from history item', () => {
    const item = {
      id: 'abc',
      query: 'restored query',
      answer: 'restored answer',
      citations: [],
      timestamp: new Date(),
    }
    useQueryStore.getState().selectHistory(item)
    const state = useQueryStore.getState()
    expect(state.query).toBe('restored query')
    expect(state.result?.answer).toBe('restored answer')
    expect(state.error).toBeNull()
  })
})

describe('queryStore — reset does not clear history', () => {
  it('preserves history on reset()', () => {
    useQueryStore.getState().addHistory('q1', 'a1', [])
    useQueryStore.getState().reset()
    expect(useQueryStore.getState().history).toHaveLength(1)
  })
})

describe('queryStore — submitQuery adds history', () => {
  it('adds entry to history after successful POST', async () => {
    mock.onPost('/v1/query').reply(200, { answer: 'test', citations: [], confidence: 0.9 })
    await useQueryStore.getState().submitQuery('my query', 'en')
    expect(useQueryStore.getState().history).toHaveLength(1)
    expect(useQueryStore.getState().history[0].query).toBe('my query')
  })

  it('does NOT add history on 429 error', async () => {
    mock.onPost('/v1/query').reply(429)
    await useQueryStore.getState().submitQuery('fail query', 'en')
    expect(useQueryStore.getState().history).toHaveLength(0)
  })
})

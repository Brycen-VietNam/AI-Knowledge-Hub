// Task: S005 T002/T003 — adminApi user CRUD + API key function tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as adminApiModule from './adminApi'

// Mock the apiClient used internally
vi.mock('./client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import { apiClient } from './client'

const mockPost = apiClient.post as ReturnType<typeof vi.fn>
const mockGet = apiClient.get as ReturnType<typeof vi.fn>
const mockDelete = apiClient.delete as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

// ── T002: createUser / deleteUser ─────────────────────────────────────────────

describe('createUser', () => {
  it('POSTs to /v1/admin/users and returns UserItem', async () => {
    const payload: adminApiModule.UserCreatePayload = {
      sub: 'alice',
      email: 'alice@example.com',
      password: 'secret123',
      group_ids: [1, 2],
    }
    const userItem: adminApiModule.UserItem = {
      id: 'u1',
      email: 'alice@example.com',
      is_active: true,
      groups: [{ id: 1, name: 'editors' }],
    }
    mockPost.mockResolvedValueOnce({ data: userItem })

    const result = await adminApiModule.createUser(payload)

    expect(mockPost).toHaveBeenCalledOnce()
    expect(mockPost).toHaveBeenCalledWith('/v1/admin/users', payload)
    expect(result).toEqual(userItem)
  })

  it('propagates HTTP errors from apiClient', async () => {
    mockPost.mockRejectedValueOnce(new Error('422 Unprocessable Entity'))
    await expect(adminApiModule.createUser({ sub: 'x', password: 'y' })).rejects.toThrow(
      '422 Unprocessable Entity',
    )
  })
})

describe('deleteUser', () => {
  it('DELETEs to /v1/admin/users/{userId}', async () => {
    mockDelete.mockResolvedValueOnce({ data: null })

    await adminApiModule.deleteUser('u1')

    expect(mockDelete).toHaveBeenCalledOnce()
    expect(mockDelete).toHaveBeenCalledWith('/v1/admin/users/u1')
  })

  it('propagates HTTP errors from apiClient', async () => {
    mockDelete.mockRejectedValueOnce(new Error('404 Not Found'))
    await expect(adminApiModule.deleteUser('missing')).rejects.toThrow('404 Not Found')
  })
})

// ── T003: generateApiKey / listApiKeys / revokeApiKey ─────────────────────────

describe('generateApiKey', () => {
  it('POSTs to /v1/admin/users/{userId}/api-keys with name', async () => {
    const created: adminApiModule.ApiKeyCreated = {
      key_id: 'k1',
      key: 'kh_abc123',
      key_prefix: 'kh_abc',
      name: 'my-key',
      created_at: '2026-04-21T00:00:00Z',
    }
    mockPost.mockResolvedValueOnce({ data: created })

    const result = await adminApiModule.generateApiKey('u1', 'my-key')

    expect(mockPost).toHaveBeenCalledWith('/v1/admin/users/u1/api-keys', { name: 'my-key' })
    expect(result).toEqual(created)
  })

  it('POSTs empty object when name is undefined', async () => {
    const created: adminApiModule.ApiKeyCreated = {
      key_id: 'k2',
      key: 'kh_def456',
      key_prefix: 'kh_def',
      name: '',
      created_at: '2026-04-21T00:00:00Z',
    }
    mockPost.mockResolvedValueOnce({ data: created })

    await adminApiModule.generateApiKey('u1')

    expect(mockPost).toHaveBeenCalledWith('/v1/admin/users/u1/api-keys', {})
  })
})

describe('listApiKeys', () => {
  it('GETs /v1/admin/users/{userId}/api-keys and unwraps items', async () => {
    const items: adminApiModule.ApiKeyItem[] = [
      { key_id: 'k1', key_prefix: 'kh_abc', name: 'my-key', created_at: '2026-04-21T00:00:00Z' },
    ]
    mockGet.mockResolvedValueOnce({ data: { items } })

    const result = await adminApiModule.listApiKeys('u1')

    expect(mockGet).toHaveBeenCalledWith('/v1/admin/users/u1/api-keys')
    expect(result).toEqual(items)
  })

  it('falls back when response has no items wrapper', async () => {
    const items: adminApiModule.ApiKeyItem[] = [
      { key_id: 'k1', key_prefix: 'kh_abc', name: 'my-key', created_at: '2026-04-21T00:00:00Z' },
    ]
    mockGet.mockResolvedValueOnce({ data: items })

    const result = await adminApiModule.listApiKeys('u1')

    expect(result).toEqual(items)
  })

  it('returns empty array for null response data', async () => {
    mockGet.mockResolvedValueOnce({ data: null })

    const result = await adminApiModule.listApiKeys('u1')

    expect(result).toEqual([])
  })
})

describe('revokeApiKey', () => {
  it('DELETEs /v1/admin/users/{userId}/api-keys/{keyId}', async () => {
    mockDelete.mockResolvedValueOnce({ data: null })

    await adminApiModule.revokeApiKey('u1', 'k1')

    expect(mockDelete).toHaveBeenCalledOnce()
    expect(mockDelete).toHaveBeenCalledWith('/v1/admin/users/u1/api-keys/k1')
  })

  it('propagates HTTP errors from apiClient', async () => {
    mockDelete.mockRejectedValueOnce(new Error('404 Not Found'))
    await expect(adminApiModule.revokeApiKey('u1', 'missing')).rejects.toThrow('404 Not Found')
  })
})

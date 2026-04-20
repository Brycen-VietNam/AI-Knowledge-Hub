// Task: T001 — adminApi.ts tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from '../../src/api/client'
import {
  listGroups,
  createGroup,
  updateGroup,
  deleteGroup,
  listUsers,
  assignGroups,
  toggleUserActive,
} from '../../src/api/adminApi'

beforeEach(() => {
  vi.restoreAllMocks()
})

const GROUPS = [
  { id: 1, name: 'editors', is_admin: false, member_count: 3 },
  { id: 2, name: 'admins', is_admin: true, member_count: 1 },
]

const USERS = [
  { id: 'u1', email: 'alice@example.com', is_active: true, groups: [{ id: 1, name: 'editors' }] },
  { id: 'u2', email: 'bob@example.com', is_active: false, groups: [] },
]

describe('listGroups', () => {
  it('returns groups array from GET /v1/admin/groups', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: GROUPS })
    const result = await listGroups()
    expect(apiClient.get).toHaveBeenCalledWith('/v1/admin/groups')
    expect(result).toEqual(GROUPS)
  })
})

describe('createGroup', () => {
  it('sends correct body to POST /v1/admin/groups', async () => {
    const newGroup = { id: 3, name: 'viewers', is_admin: false, member_count: 0 }
    vi.spyOn(apiClient, 'post').mockResolvedValue({ data: newGroup })
    const result = await createGroup('viewers', false)
    expect(apiClient.post).toHaveBeenCalledWith('/v1/admin/groups', { name: 'viewers', is_admin: false })
    expect(result).toEqual(newGroup)
  })
})

describe('updateGroup', () => {
  it('sends correct body to PUT /v1/admin/groups/{id}', async () => {
    const updated = { id: 1, name: 'writers', is_admin: false, member_count: 3 }
    vi.spyOn(apiClient, 'put').mockResolvedValue({ data: updated })
    const result = await updateGroup(1, 'writers', false)
    expect(apiClient.put).toHaveBeenCalledWith('/v1/admin/groups/1', { name: 'writers', is_admin: false })
    expect(result).toEqual(updated)
  })
})

describe('deleteGroup', () => {
  it('calls DELETE /v1/admin/groups/{id}', async () => {
    vi.spyOn(apiClient, 'delete').mockResolvedValue({ data: undefined })
    await deleteGroup(1)
    expect(apiClient.delete).toHaveBeenCalledWith('/v1/admin/groups/1')
  })

  it('propagates 409 error without swallowing', async () => {
    const err = { response: { status: 409 } }
    vi.spyOn(apiClient, 'delete').mockRejectedValue(err)
    await expect(deleteGroup(1)).rejects.toEqual(err)
  })
})

describe('listUsers', () => {
  it('calls GET /v1/admin/users without params when search is undefined', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: USERS })
    const result = await listUsers()
    expect(apiClient.get).toHaveBeenCalledWith('/v1/admin/users', { params: undefined })
    expect(result).toEqual(USERS)
  })

  it('passes search param when provided', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: [USERS[0]] })
    await listUsers('alice')
    expect(apiClient.get).toHaveBeenCalledWith('/v1/admin/users', { params: { search: 'alice' } })
  })
})

describe('assignGroups', () => {
  it('sends correct body to POST /v1/admin/users/{userId}/groups', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValue({ data: undefined })
    await assignGroups('u1', [1, 2])
    expect(apiClient.post).toHaveBeenCalledWith('/v1/admin/users/u1/groups', { group_ids: [1, 2] })
  })
})

describe('toggleUserActive', () => {
  it('sends correct body to PUT /v1/admin/users/{userId}', async () => {
    vi.spyOn(apiClient, 'put').mockResolvedValue({ data: undefined })
    await toggleUserActive('u1', false)
    expect(apiClient.put).toHaveBeenCalledWith('/v1/admin/users/u1', { is_active: false })
  })
})

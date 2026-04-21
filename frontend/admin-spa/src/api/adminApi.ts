// Spec: docs/admin-spa/spec/admin-spa.spec.md#S003
// Task: T001 — adminApi.ts — groups + users API client
import { apiClient } from './client'

export interface GroupItem {
  id: number
  name: string
  is_admin: boolean
  member_count: number
}

export interface UserItem {
  id: string
  email: string
  is_active: boolean
  groups: { id: number; name: string }[]
}

export async function listGroups(): Promise<GroupItem[]> {
  const response = await apiClient.get('/v1/admin/groups')
  const items = response.data?.items ?? response.data ?? []
  // backend returns user_count; map to member_count for UI
  return items.map((g: GroupItem & { user_count?: number }) => ({
    ...g,
    member_count: g.member_count ?? g.user_count ?? 0,
  }))
}

export async function createGroup(name: string, is_admin: boolean): Promise<GroupItem> {
  const response = await apiClient.post('/v1/admin/groups', { name, is_admin })
  return response.data
}

export async function updateGroup(id: number, name: string, is_admin: boolean): Promise<GroupItem> {
  const response = await apiClient.put(`/v1/admin/groups/${id}`, { name, is_admin })
  return response.data
}

export async function deleteGroup(id: number): Promise<void> {
  await apiClient.delete(`/v1/admin/groups/${id}`)
}

export async function listUsers(search?: string): Promise<UserItem[]> {
  const response = await apiClient.get('/v1/admin/users', {
    params: search ? { search } : undefined,
  })
  return response.data?.items ?? response.data ?? []
}

export async function assignGroups(userId: string, groupIds: number[]): Promise<void> {
  await apiClient.post(`/v1/admin/users/${userId}/groups`, { group_ids: groupIds })
}

export async function toggleUserActive(userId: string, is_active: boolean): Promise<void> {
  await apiClient.put(`/v1/admin/users/${userId}`, { is_active })
}

export interface UserCreatePayload {
  sub: string
  email?: string
  display_name?: string
  password: string
  group_ids?: number[]
}

export interface ApiKeyCreated {
  key_id: string
  key: string          // plaintext — present only on create
  key_prefix: string
  name: string
  created_at: string
}

export interface ApiKeyItem {
  key_id: string
  key_prefix: string
  name: string
  created_at: string   // no `key` field
}

export async function createUser(payload: UserCreatePayload): Promise<UserItem> {
  const response = await apiClient.post('/v1/admin/users', payload)
  return response.data
}

export async function deleteUser(userId: string): Promise<void> {
  await apiClient.delete(`/v1/admin/users/${userId}`)
}

export async function generateApiKey(userId: string, name?: string): Promise<ApiKeyCreated> {
  const response = await apiClient.post(`/v1/admin/users/${userId}/api-keys`, name ? { name } : {})
  return response.data
}

export async function listApiKeys(userId: string): Promise<ApiKeyItem[]> {
  const response = await apiClient.get(`/v1/admin/users/${userId}/api-keys`)
  return response.data?.items ?? response.data ?? []
}

export async function revokeApiKey(userId: string, keyId: string): Promise<void> {
  await apiClient.delete(`/v1/admin/users/${userId}/api-keys/${keyId}`)
}

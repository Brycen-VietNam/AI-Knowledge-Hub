// Task: T001 — documentsApi.ts tests
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { apiClient } from '../../src/api/client'
import { listDocuments, uploadDocument, deleteDocument } from '../../src/api/documentsApi'
import { useAuthStore } from '../../src/store/authStore'

const mock = new MockAdapter(apiClient)

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

describe('listDocuments', () => {
  it('calls GET /v1/admin/documents and returns data', async () => {
    const payload = { items: [], total: 0, limit: 20, offset: 0 }
    mock.onGet('/v1/admin/documents').reply(200, payload)
    const result = await listDocuments()
    expect(result).toEqual(payload)
  })

  it('passes limit + offset as query params', async () => {
    mock.onGet('/v1/admin/documents').reply(200, { items: [], total: 0, limit: 10, offset: 20 })
    await listDocuments({ limit: 10, offset: 20 })
    const params = mock.history.get[0].params
    expect(params.limit).toBe(10)
    expect(params.offset).toBe(20)
  })

  it('passes status filter param', async () => {
    mock.onGet('/v1/admin/documents').reply(200, { items: [], total: 0, limit: 20, offset: 0 })
    await listDocuments({ status: 'ready' })
    expect(mock.history.get[0].params.status).toBe('ready')
  })

  it('passes lang filter param', async () => {
    mock.onGet('/v1/admin/documents').reply(200, { items: [], total: 0, limit: 20, offset: 0 })
    await listDocuments({ lang: 'ja' })
    expect(mock.history.get[0].params.lang).toBe('ja')
  })

  it('maps userGroupId → user_group_id snake_case param', async () => {
    mock.onGet('/v1/admin/documents').reply(200, { items: [], total: 0, limit: 20, offset: 0 })
    await listDocuments({ userGroupId: 5 })
    expect(mock.history.get[0].params.user_group_id).toBe(5)
    expect(mock.history.get[0].params.userGroupId).toBeUndefined()
  })

  it('omits undefined optional params', async () => {
    mock.onGet('/v1/admin/documents').reply(200, { items: [], total: 0, limit: 20, offset: 0 })
    await listDocuments({})
    const params = mock.history.get[0].params
    expect(params.status).toBeUndefined()
    expect(params.lang).toBeUndefined()
    expect(params.user_group_id).toBeUndefined()
  })
})

describe('uploadDocument', () => {
  it('calls POST /v1/documents/upload and returns doc_id', async () => {
    mock.onPost('/v1/documents/upload').reply(202, {
      doc_id: 'abc-123',
      status: 'processing',
      source_url: null,
    })
    const file = new File(['hello'], 'report.txt', { type: 'text/plain' })
    const result = await uploadDocument(file)
    expect(result.doc_id).toBe('abc-123')
    expect(result.status).toBe('processing')
    expect(result.source_url).toBeNull()
  })

  it('appends file to FormData', async () => {
    mock.onPost('/v1/documents/upload').reply(202, { doc_id: 'x', status: 'processing', source_url: null })
    const file = new File(['data'], 'doc.txt', { type: 'text/plain' })
    await uploadDocument(file)
    const body = mock.history.post[0].data as FormData
    expect(body.get('file')).toBe(file)
  })

  it('appends optional title, lang, groupId, sourceUrl to FormData', async () => {
    mock.onPost('/v1/documents/upload').reply(202, { doc_id: 'x', status: 'processing', source_url: 'https://example.com' })
    const file = new File(['data'], 'doc.txt', { type: 'text/plain' })
    await uploadDocument(file, 'My Doc', 'ja', 3, 'https://example.com')
    const body = mock.history.post[0].data as FormData
    expect(body.get('title')).toBe('My Doc')
    expect(body.get('lang')).toBe('ja')
    expect(body.get('user_group_id')).toBe('3')
    expect(body.get('source_url')).toBe('https://example.com')
  })

  it('omits optional fields when not provided', async () => {
    mock.onPost('/v1/documents/upload').reply(202, { doc_id: 'x', status: 'processing', source_url: null })
    const file = new File(['data'], 'doc.txt', { type: 'text/plain' })
    await uploadDocument(file)
    const body = mock.history.post[0].data as FormData
    expect(body.get('title')).toBeNull()
    expect(body.get('source_url')).toBeNull()
  })
})

describe('deleteDocument', () => {
  it('calls DELETE /v1/admin/documents/{id} and returns void', async () => {
    mock.onDelete('/v1/admin/documents/doc-999').reply(204)
    const result = await deleteDocument('doc-999')
    expect(result).toBeUndefined()
    expect(mock.history.delete[0].url).toBe('/v1/admin/documents/doc-999')
  })
})

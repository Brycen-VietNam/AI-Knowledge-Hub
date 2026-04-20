// Spec: docs/admin-spa/spec/admin-spa.spec.md#S002
// Task: T001 — documentsApi.ts — 3 API functions + TypeScript types
// Decision: D06 — upload via multipart/form-data (not JSON)
// Decision: D11 — response key is doc_id (not document_id)
// Gap: G4 — source_url exposed (migration 007 already exists)
import { apiClient } from './client'

export interface DocumentItem {
  id: string
  title: string
  lang: string
  user_group_id: number | null
  user_group_name?: string
  status: 'pending' | 'processing' | 'ready' | 'error'
  created_at: string
  chunk_count: number
  source_url: string | null
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
  limit: number
  offset: number
}

export interface ListDocumentsParams {
  limit?: number
  offset?: number
  status?: string
  lang?: string
  userGroupId?: number
}

export interface UploadDocumentResponse {
  doc_id: string
  status: string
  source_url: string | null
}

export async function listDocuments(params: ListDocumentsParams = {}): Promise<DocumentListResponse> {
  const response = await apiClient.get('/v1/admin/documents', {
    params: {
      limit: params.limit,
      offset: params.offset,
      ...(params.status ? { status: params.status } : {}),
      ...(params.lang ? { lang: params.lang } : {}),
      ...(params.userGroupId != null ? { user_group_id: params.userGroupId } : {}),
    },
  })
  return response.data
}

export async function uploadDocument(
  file: File,
  title?: string,
  lang?: string,
  groupId?: number,
  sourceUrl?: string,
): Promise<UploadDocumentResponse> {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)
  if (lang) form.append('lang', lang)
  if (groupId != null) form.append('user_group_id', String(groupId))
  if (sourceUrl) form.append('source_url', sourceUrl)
  const response = await apiClient.post('/v1/documents/upload', form)
  return response.data
}

export async function deleteDocument(docId: string): Promise<void> {
  await apiClient.delete(`/v1/admin/documents/${docId}`)
}

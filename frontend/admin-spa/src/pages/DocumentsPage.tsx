// Spec: docs/admin-spa/spec/admin-spa.spec.md#S002
// Task: T006 — DocumentsPage — orchestration: table + upload modal + delete dialog + pagination + filter
// Decision: D06 — upload via UploadModal (multipart), D11 — doc_id key
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminGuard } from '../hooks/useAdminGuard'
import { listDocuments, deleteDocument } from '../api/documentsApi'
import type { DocumentItem } from '../api/documentsApi'
import { apiClient } from '../api/client'
import { DocumentTable } from '../components/DocumentTable'
import { DeleteConfirmDialog } from '../components/DeleteConfirmDialog'
import { UploadModal } from '../components/UploadModal'

const LIMIT = 20

export function DocumentsPage() {
  const { t } = useTranslation()
  useAdminGuard()

  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterLang, setFilterLang] = useState('')
  const [filterGroup, setFilterGroup] = useState<number | undefined>()
  const [uploadOpen, setUploadOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([])
  const [fetchError, setFetchError] = useState(false)

  // Fetch groups once on mount (inline — avoids importing S003 module not yet implemented)
  useEffect(() => {
    apiClient.get('/v1/admin/groups').then((res) => {
      const items = res.data?.items ?? res.data ?? []
      setGroups(items.map((g: { id: number; name: string }) => ({ id: g.id, name: g.name })))
    }).catch(() => {
      // Groups unavailable — upload modal will show no group options
    })
  }, [])

  const fetchDocuments = useCallback(() => {
    listDocuments({
      limit: LIMIT,
      offset,
      ...(filterStatus ? { status: filterStatus } : {}),
      ...(filterLang ? { lang: filterLang } : {}),
      ...(filterGroup != null ? { userGroupId: filterGroup } : {}),
    }).then((res) => {
      setDocuments(res.items)
      setTotal(res.total)
      setFetchError(false)
    }).catch(() => {
      setFetchError(true)
    })
  }, [offset, filterStatus, filterLang, filterGroup])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Toast auto-dismiss
  useEffect(() => {
    if (!toastMessage) return
    const timer = setTimeout(() => setToastMessage(null), 3000)
    return () => clearTimeout(timer)
  }, [toastMessage])

  function handleFilterStatus(val: string) {
    setFilterStatus(val)
    setOffset(0)
  }
  function handleFilterLang(val: string) {
    setFilterLang(val)
    setOffset(0)
  }
  function handleFilterGroup(val: string) {
    setFilterGroup(val ? Number(val) : undefined)
    setOffset(0)
  }

  function handleDelete(id: string, title: string) {
    setDeleteTarget({ id, title })
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await deleteDocument(deleteTarget.id)
      setDocuments((prev) => prev.filter((d) => d.id !== deleteTarget.id))
      setTotal((prev) => prev - 1)
    } catch {
      // Delete failed — leave list unchanged
    } finally {
      setDeleteTarget(null)
    }
  }

  function handleUploadSuccess() {
    setToastMessage(t('documents.upload_success'))
    fetchDocuments()
  }

  return (
    <main className="documents-page">
      <div className="documents-header">
        <h1>{t('documents.page_title')}</h1>
        <button className="btn-primary" onClick={() => setUploadOpen(true)}>
          {t('documents.upload_btn')}
        </button>
      </div>

      <div className="documents-filters">
        <select
          aria-label={t('documents.filter_status')}
          value={filterStatus}
          onChange={(e) => handleFilterStatus(e.target.value)}
        >
          <option value="">{t('documents.filter_status')}: {t('documents.filter_all')}</option>
          <option value="pending">{t('documents.status_pending')}</option>
          <option value="processing">{t('documents.status_processing')}</option>
          <option value="ready">{t('documents.status_ready')}</option>
          <option value="error">{t('documents.status_error')}</option>
        </select>

        <select
          aria-label={t('documents.filter_lang')}
          value={filterLang}
          onChange={(e) => handleFilterLang(e.target.value)}
        >
          <option value="">{t('documents.filter_lang')}: {t('documents.filter_all')}</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="vi">Tiếng Việt</option>
          <option value="ko">한국어</option>
        </select>

        <select
          aria-label={t('documents.filter_group')}
          value={filterGroup ?? ''}
          onChange={(e) => handleFilterGroup(e.target.value)}
        >
          <option value="">{t('documents.filter_group')}: {t('documents.filter_all')}</option>
          {groups.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      {fetchError && (
        <p className="fetch-error">{t('documents.fetch_error')}</p>
      )}

      <DocumentTable documents={documents} onDelete={handleDelete} />

      <div className="pagination">
        <button
          className="btn-secondary"
          disabled={offset === 0}
          onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}
        >
          {t('documents.prev')}
        </button>
        <button
          className="btn-secondary"
          disabled={offset + LIMIT >= total}
          onClick={() => setOffset((o) => o + LIMIT)}
        >
          {t('documents.next')}
        </button>
      </div>

      <UploadModal
        open={uploadOpen}
        groups={groups}
        onClose={() => setUploadOpen(false)}
        onSuccess={handleUploadSuccess}
      />

      <DeleteConfirmDialog
        open={deleteTarget !== null}
        title={t('documents.delete_confirm_title')}
        message={t('documents.delete_confirm_msg', { title: deleteTarget?.title ?? '' })}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />

      {toastMessage && (
        <div className="toast toast-success">{toastMessage}</div>
      )}
    </main>
  )
}

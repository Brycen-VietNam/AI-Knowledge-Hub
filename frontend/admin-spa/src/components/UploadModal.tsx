// Spec: docs/admin-spa/spec/admin-spa.spec.md#S002
// Task: T004 — UploadModal — file input upload (D06) with source_url (G4)
// Decision: D06 — file input (.pdf/.docx/.html/.txt/.md), multipart/form-data
// Decision: D11 — response key is doc_id
// Gap: G4 — source_url optional field
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { uploadDocument } from '../api/documentsApi'

interface UploadModalProps {
  open: boolean
  groups: { id: number; name: string }[]
  onClose: () => void
  onSuccess: () => void
}

export function UploadModal({ open, groups, onClose, onSuccess }: UploadModalProps) {
  const { t } = useTranslation()

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [lang, setLang] = useState('')
  const [groupId, setGroupId] = useState<number | undefined>()
  const [sourceUrl, setSourceUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null
    setFile(selected)
    if (selected) {
      setTitle(selected.name.replace(/\.[^.]+$/, ''))
    }
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)
    try {
      await uploadDocument(
        file,
        title || undefined,
        lang || undefined,
        groupId,
        sourceUrl || undefined,
      )
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 413) {
        setError(t('documents.upload_error_too_large'))
      } else if (status === 415) {
        setError(t('documents.upload_error_unsupported'))
      } else {
        setError(t('documents.upload_error_generic'))
      }
    } finally {
      setLoading(false)
    }
  }

  function handleOverlayClick() {
    if (!loading) onClose()
  }

  return (
    <div className="confirm-dialog-overlay" onClick={handleOverlayClick}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{t('documents.upload_modal_title')}</h2>
        <form onSubmit={handleSubmit} className="upload-form">
          <div className="upload-field">
            <label>{t('documents.upload_file_label')}</label>
            <input
              type="file"
              accept=".pdf,.docx,.html,.txt,.md"
              onChange={handleFileChange}
              required
            />
            <span className="upload-file-hint">{t('documents.upload_file_hint')}</span>
          </div>

          <div className="upload-field">
            <label>{t('documents.upload_title_label')}</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('documents.upload_title_label')}
            />
          </div>

          <div className="upload-field">
            <label>{t('documents.upload_lang_label')}</label>
            <select value={lang} onChange={(e) => setLang(e.target.value)}>
              <option value="">{t('documents.upload_lang_auto')}</option>
              <option value="en">English</option>
              <option value="ja">日本語</option>
              <option value="vi">Tiếng Việt</option>
              <option value="ko">한국어</option>
            </select>
          </div>

          <div className="upload-field">
            <label>{t('documents.upload_group_label')}</label>
            <select
              value={groupId ?? ''}
              onChange={(e) => setGroupId(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">{t('documents.no_group')}</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>{g.name}</option>
              ))}
            </select>
          </div>

          <div className="upload-field">
            <label>{t('documents.upload_source_url_label')}</label>
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder={t('documents.upload_source_url_label')}
            />
          </div>

          {error && <p className="upload-error">{error}</p>}

          <div className="confirm-dialog-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              {t('documents.upload_cancel')}
            </button>
            <button type="submit" className="btn-primary" disabled={!file || loading}>
              {loading ? t('documents.upload_loading') : t('documents.upload_submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

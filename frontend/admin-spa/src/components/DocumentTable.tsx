// Spec: docs/admin-spa/spec/admin-spa.spec.md#S002
// Task: T003 — DocumentTable — 7-column table + status badge + empty state
import { useTranslation } from 'react-i18next'
import type { DocumentItem } from '../api/documentsApi'

interface DocumentTableProps {
  documents: DocumentItem[]
  onDelete: (id: string, title: string) => void
}

function StatusBadge({ status }: { status: DocumentItem['status'] }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

export function DocumentTable({ documents, onDelete }: DocumentTableProps) {
  const { t } = useTranslation()

  if (documents.length === 0) {
    return <p className="table-empty">{t('documents.empty')}</p>
  }

  return (
    <table className="documents-table">
      <thead>
        <tr>
          <th>{t('documents.col_title')}</th>
          <th>{t('documents.col_lang')}</th>
          <th>{t('documents.col_group')}</th>
          <th>{t('documents.col_status')}</th>
          <th>{t('documents.col_created_at')}</th>
          <th>{t('documents.col_chunks')}</th>
          <th>{t('documents.col_source_url')}</th>
          <th>{t('documents.col_actions')}</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <tr key={doc.id}>
            <td>{doc.title}</td>
            <td>{doc.lang}</td>
            <td>{doc.user_group_name ?? t('documents.no_group')}</td>
            <td><StatusBadge status={doc.status} /></td>
            <td>{new Date(doc.created_at).toLocaleDateString()}</td>
            <td>{doc.chunk_count}</td>
            <td>
              {doc.source_url
                ? <a href={doc.source_url} target="_blank" rel="noopener noreferrer" className="source-url-link">{doc.source_url}</a>
                : <span className="text-muted">—</span>}
            </td>
            <td>
              <button
                className="btn-icon btn-danger"
                onClick={() => onDelete(doc.id, doc.title)}
              >
                {t('documents.delete_btn')}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

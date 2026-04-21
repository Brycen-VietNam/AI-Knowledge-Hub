// Spec: docs/user-management/spec/user-management.spec.md#S007
// Task: S007 T001/T002/T003 — ApiKeyPanel — list, generate (one-time show), revoke per user
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import type { ApiKeyItem, ApiKeyCreated } from '../api/adminApi'
import { listApiKeys, generateApiKey, revokeApiKey } from '../api/adminApi'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'

interface Props {
  userId: string
}

export function ApiKeyPanel({ userId }: Props) {
  const { t } = useTranslation()

  const [keys, setKeys] = useState<ApiKeyItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Generate flow
  const [keyName, setKeyName] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedKey, setGeneratedKey] = useState<string | null>(null)
  const [generateError, setGenerateError] = useState<string | null>(null)

  // Revoke flow
  const [revokingKey, setRevokingKey] = useState<ApiKeyItem | null>(null)
  const [isRevoking, setIsRevoking] = useState(false)
  const [revokeError, setRevokeError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    listApiKeys(userId)
      .then((items) => { if (!cancelled) setKeys(items) })
      .catch(() => { if (!cancelled) setError(t('api_key.load_error')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [userId, t])

  async function handleGenerate() {
    setGenerateError(null)
    setIsGenerating(true)
    try {
      const result: ApiKeyCreated = await generateApiKey(userId, keyName.trim() || undefined)
      // Append new item (without key field) to list
      const newItem: ApiKeyItem = {
        key_id: result.key_id,
        key_prefix: result.key_prefix,
        name: result.name,
        created_at: result.created_at,
      }
      setKeys((prev) => [...prev, newItem])
      setGeneratedKey(result.key)
      setKeyName('')
    } catch {
      setGenerateError(t('api_key.generate_error'))
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleRevoke() {
    if (!revokingKey) return
    setIsRevoking(true)
    setRevokeError(null)
    try {
      await revokeApiKey(userId, revokingKey.key_id)
      setKeys((prev) => prev.filter((k) => k.key_id !== revokingKey.key_id))
      setRevokingKey(null)
    } catch {
      setRevokeError(t('api_key.revoke_error'))
      setRevokingKey(null)
    } finally {
      setIsRevoking(false)
    }
  }

  return (
    <div className="api-key-panel">
      <h3>{t('api_key.panel_title')}</h3>

      {loading && <p className="loading-state">{t('api_key.loading')}</p>}

      {!loading && (
        <>
          {keys.length === 0 && <p className="empty-state">{t('api_key.empty')}</p>}

          {keys.length > 0 && (
            <table className="api-key-table">
              <thead>
                <tr>
                  <th>{t('api_key.col_prefix')}</th>
                  <th>{t('api_key.col_name')}</th>
                  <th>{t('api_key.col_created_at')}</th>
                  <th>{t('api_key.col_actions')}</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.key_id}>
                    <td><code>{k.key_prefix}</code></td>
                    <td>{k.name}</td>
                    <td>{new Date(k.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn-danger"
                        onClick={() => { setRevokingKey(k); setRevokeError(null) }}
                        disabled={isRevoking}
                      >
                        {t('api_key.btn_revoke')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Generate section */}
          <div className="api-key-generate">
            <input
              type="text"
              value={keyName}
              placeholder={t('api_key.name_placeholder')}
              onChange={(e) => setKeyName(e.target.value)}
              disabled={isGenerating}
            />
            <button
              className="btn-primary"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              {t('api_key.btn_generate')}
            </button>
          </div>

          {generateError && <p className="form-error">{generateError}</p>}
          {revokeError && <p className="form-error">{revokeError}</p>}
          {error && <p className="form-error">{error}</p>}
        </>
      )}

      {/* One-time key dialog */}
      {generatedKey !== null && (
        <div className="confirm-dialog-overlay">
          <div className="confirm-dialog api-key-dialog" onClick={(e) => e.stopPropagation()}>
            <h2>{t('api_key.one_time_title')}</h2>
            <p className="one-time-warning">{t('api_key.one_time_warning')}</p>
            <code className="api-key-value">{generatedKey}</code>
            <div className="confirm-dialog-actions">
              <button
                className="btn-secondary"
                onClick={() => navigator.clipboard.writeText(generatedKey)}
              >
                {t('api_key.btn_copy')}
              </button>
              <button
                className="btn-primary"
                onClick={() => { setGeneratedKey(null) }}
              >
                {t('api_key.btn_dismiss')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Revoke confirm dialog */}
      <DeleteConfirmDialog
        open={revokingKey !== null}
        title={t('api_key.revoke_title')}
        message={t('api_key.revoke_message', { prefix: revokingKey?.key_prefix ?? '' })}
        onConfirm={handleRevoke}
        onCancel={() => setRevokingKey(null)}
      />
    </div>
  )
}

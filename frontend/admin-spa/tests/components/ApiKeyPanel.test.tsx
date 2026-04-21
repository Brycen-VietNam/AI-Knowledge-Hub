// Task: S007 T004 — ApiKeyPanel full AC coverage
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { ApiKeyPanel } from '../../src/components/ApiKeyPanel'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

const KEYS: adminApi.ApiKeyItem[] = [
  { key_id: 'k1', key_prefix: 'kh_abc', name: 'ci-bot', created_at: '2026-04-21T00:00:00Z' },
  { key_id: 'k2', key_prefix: 'kh_def', name: 'read-only', created_at: '2026-04-20T00:00:00Z' },
]

const CREATED: adminApi.ApiKeyCreated = {
  key_id: 'k3',
  key: 'kh_newkeyplaintext123456789abcdef',
  key_prefix: 'kh_new',
  name: 'new-key',
  created_at: '2026-04-21T12:00:00Z',
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('ApiKeyPanel', () => {
  it('shows loading state on mount', () => {
    vi.spyOn(adminApi, 'listApiKeys').mockReturnValue(new Promise(() => {}))
    render(<ApiKeyPanel userId="u1" />)
    expect(document.querySelector('.loading-state')).toBeTruthy()
  })

  it('renders key list with prefix, name, created_at', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => {
      expect(screen.getByText('kh_abc')).toBeTruthy()
      expect(screen.getByText('ci-bot')).toBeTruthy()
      expect(screen.getByText('kh_def')).toBeTruthy()
      expect(screen.getByText('read-only')).toBeTruthy()
    })
  })

  it('does not render key_hash (no 64-char hex string in DOM)', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(screen.queryByText(/loading/i)).toBeNull())
    // 64-char hex = SHA-256 hash pattern
    const hex64 = /\b[0-9a-f]{64}\b/i
    expect(document.body.textContent).not.toMatch(hex64)
  })

  it('shows empty state when no keys', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => {
      expect(document.querySelector('.empty-state')).toBeTruthy()
    })
  })

  it('generate key shows one-time dialog with plaintext key', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    vi.spyOn(adminApi, 'generateApiKey').mockResolvedValue(CREATED)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(document.querySelector('.loading-state')).toBeNull())
    fireEvent.click(screen.getByText('Generate Key'))
    await waitFor(() => {
      expect(document.querySelector('.api-key-value')).toBeTruthy()
      expect(document.querySelector('.api-key-value')!.textContent).toBe(CREATED.key)
    })
  })

  it('one-time warning message is visible in dialog', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    vi.spyOn(adminApi, 'generateApiKey').mockResolvedValue(CREATED)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(document.querySelector('.loading-state')).toBeNull())
    fireEvent.click(screen.getByText('Generate Key'))
    await waitFor(() => {
      expect(document.querySelector('.one-time-warning')).toBeTruthy()
    })
  })

  it('copy to clipboard calls navigator.clipboard.writeText', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    vi.spyOn(adminApi, 'generateApiKey').mockResolvedValue(CREATED)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(document.querySelector('.loading-state')).toBeNull())
    fireEvent.click(screen.getByText('Generate Key'))
    await waitFor(() => expect(document.querySelector('.api-key-value')).toBeTruthy())
    fireEvent.click(screen.getByText("Copy"))
    expect(writeText).toHaveBeenCalledWith(CREATED.key)
  })

  it('dismiss clears plaintext key from DOM', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue([])
    vi.spyOn(adminApi, 'generateApiKey').mockResolvedValue(CREATED)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(document.querySelector('.loading-state')).toBeNull())
    fireEvent.click(screen.getByText('Generate Key'))
    await waitFor(() => expect(document.querySelector('.api-key-value')).toBeTruthy())
    fireEvent.click(screen.getByText("I've copied it"))
    await waitFor(() => {
      expect(document.querySelector('.api-key-value')).toBeNull()
      expect(document.querySelector('.api-key-dialog')).toBeNull()
    })
  })

  it('after generate: new key item appended to list (no full refetch)', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    vi.spyOn(adminApi, 'generateApiKey').mockResolvedValue(CREATED)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(screen.getByText('kh_abc')).toBeTruthy())
    fireEvent.click(screen.getByText('Generate Key'))
    await waitFor(() => expect(document.querySelector('.api-key-value')).toBeTruthy())
    // The new prefix should also be in the table (appended)
    expect(screen.getByText('kh_new')).toBeTruthy()
    // listApiKeys only called once (mount), not again after generate
    expect(adminApi.listApiKeys).toHaveBeenCalledTimes(1)
  })

  it('revoke opens DeleteConfirmDialog', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(screen.getByText('kh_abc')).toBeTruthy())
    const revokeButtons = screen.getAllByText('Revoke')
    fireEvent.click(revokeButtons[0])
    await waitFor(() => {
      expect(document.querySelector('.confirm-dialog')).toBeTruthy()
    })
  })

  it('confirm revoke removes key from list', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    vi.spyOn(adminApi, 'revokeApiKey').mockResolvedValue()
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(screen.getByText('kh_abc')).toBeTruthy())
    const revokeButtons = screen.getAllByText('Revoke')
    fireEvent.click(revokeButtons[0])
    await waitFor(() => expect(document.querySelector('.confirm-dialog')).toBeTruthy())
    // Click the Delete button in the confirm dialog
    fireEvent.click(document.querySelector('.confirm-dialog .btn-danger')!)
    await waitFor(() => {
      expect(screen.queryByText('kh_abc')).toBeNull()
      expect(screen.getByText('kh_def')).toBeTruthy()
    })
  })

  it('cancel revoke keeps key in list and closes dialog', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(screen.getByText('kh_abc')).toBeTruthy())
    const revokeButtons = screen.getAllByText('Revoke')
    fireEvent.click(revokeButtons[0])
    await waitFor(() => expect(document.querySelector('.confirm-dialog')).toBeTruthy())
    fireEvent.click(document.querySelector('.confirm-dialog .btn-secondary')!)
    await waitFor(() => {
      expect(document.querySelector('.confirm-dialog')).toBeNull()
      expect(screen.getByText('kh_abc')).toBeTruthy()
    })
  })

  it('revoke failure shows inline error, key stays in list', async () => {
    vi.spyOn(adminApi, 'listApiKeys').mockResolvedValue(KEYS)
    vi.spyOn(adminApi, 'revokeApiKey').mockRejectedValue(new Error('500'))
    render(<ApiKeyPanel userId="u1" />)
    await waitFor(() => expect(screen.getByText('kh_abc')).toBeTruthy())
    const revokeButtons = screen.getAllByText('Revoke')
    fireEvent.click(revokeButtons[0])
    await waitFor(() => expect(document.querySelector('.confirm-dialog')).toBeTruthy())
    fireEvent.click(document.querySelector('.confirm-dialog .btn-danger')!)
    await waitFor(() => {
      expect(document.querySelector('.form-error')).toBeTruthy()
      expect(screen.getByText('kh_abc')).toBeTruthy()
    })
  })
})

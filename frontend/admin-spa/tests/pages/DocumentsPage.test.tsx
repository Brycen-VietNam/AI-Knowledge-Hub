// Task: T006 — DocumentsPage tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { DocumentsPage } from '../../src/pages/DocumentsPage'
import * as documentsApi from '../../src/api/documentsApi'
import * as clientModule from '../../src/api/client'
import { useAuthStore } from '../../src/store/authStore'
import type { DocumentItem, DocumentListResponse } from '../../src/api/documentsApi'
import '../../src/i18n'

// Stub useAdminGuard — no redirect side-effects in tests
vi.mock('../../src/hooks/useAdminGuard', () => ({ useAdminGuard: vi.fn() }))

const makeDoc = (overrides: Partial<DocumentItem> = {}): DocumentItem => ({
  id: 'doc-1',
  title: 'Test Doc',
  lang: 'en',
  user_group_id: null,
  status: 'ready',
  created_at: '2026-04-20T00:00:00',
  chunk_count: 3,
  source_url: null,
  ...overrides,
})

const makeListResponse = (docs: DocumentItem[], total?: number): DocumentListResponse => ({
  items: docs,
  total: total ?? docs.length,
  limit: 20,
  offset: 0,
})

beforeEach(() => {
  vi.restoreAllMocks()
  useAuthStore.setState({
    token: 'test-token',
    username: 'admin',
    isAdmin: true,
    sessionExpiredMessage: null,
    _refreshTimer: null,
  })
  // Default: groups fetch returns empty
  vi.spyOn(clientModule.apiClient, 'get').mockResolvedValue({ data: { items: [] } })
})

describe('DocumentsPage', () => {
  it('renders page title and upload button', async () => {
    vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse([]))
    await act(async () => {
      render(<DocumentsPage />)
    })
    expect(screen.getByText('Documents')).toBeTruthy()
    expect(screen.getByText('Upload Document')).toBeTruthy()
  })

  it('fetches and renders documents on mount', async () => {
    const docs = [makeDoc({ id: 'a', title: 'Alpha' }), makeDoc({ id: 'b', title: 'Beta' })]
    vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse(docs))

    await act(async () => {
      render(<DocumentsPage />)
    })

    await waitFor(() => {
      expect(screen.getByText('Alpha')).toBeTruthy()
      expect(screen.getByText('Beta')).toBeTruthy()
    })
  })

  it('re-fetches when status filter changes', async () => {
    const listSpy = vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse([]))

    await act(async () => {
      render(<DocumentsPage />)
    })

    const statusSelect = screen.getAllByRole('combobox')[0]
    await act(async () => {
      fireEvent.change(statusSelect, { target: { value: 'ready' } })
    })

    await waitFor(() => {
      expect(listSpy).toHaveBeenCalledTimes(2)
      const lastCall = listSpy.mock.calls[1][0]
      expect(lastCall.status).toBe('ready')
    })
  })

  it('opens delete dialog and calls deleteDocument on confirm', async () => {
    const doc = makeDoc({ id: 'doc-42', title: 'To Delete' })
    vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse([doc]))
    const deleteSpy = vi.spyOn(documentsApi, 'deleteDocument').mockResolvedValue(undefined)

    await act(async () => {
      render(<DocumentsPage />)
    })

    await waitFor(() => {
      expect(screen.getByText('To Delete')).toBeTruthy()
    })

    // Click delete button in table
    fireEvent.click(screen.getByText('Delete'))

    // Confirm dialog should appear
    await waitFor(() => {
      expect(document.querySelector('.confirm-dialog')).toBeTruthy()
    })

    // Confirm
    await act(async () => {
      const confirmBtn = document.querySelector('.confirm-dialog .btn-danger') as HTMLElement
      fireEvent.click(confirmBtn)
    })

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith('doc-42')
      expect(screen.queryByText('To Delete')).toBeNull()
    })
  })

  it('shows upload success toast after upload', async () => {
    vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse([]))

    await act(async () => {
      render(<DocumentsPage />)
    })

    // Open upload modal
    fireEvent.click(screen.getByText('Upload Document'))

    // Simulate onSuccess by calling it via modal's internal callback —
    // mock uploadDocument to resolve immediately
    vi.spyOn(documentsApi, 'uploadDocument').mockResolvedValue({
      doc_id: 'new-doc',
      status: 'processing',
      source_url: null,
    })

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [new File(['x'], 'test.pdf', { type: 'application/pdf' })] } })

    await act(async () => {
      fireEvent.submit(document.querySelector('form')!)
    })

    await waitFor(() => {
      expect(screen.getByText('Document uploaded successfully')).toBeTruthy()
    })
  })

  it('disables Prev button when offset=0', async () => {
    vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse([], 100))

    await act(async () => {
      render(<DocumentsPage />)
    })

    await waitFor(() => {
      const prevBtn = screen.getByText('Previous') as HTMLButtonElement
      expect(prevBtn.disabled).toBe(true)
    })
  })

  it('disables Next button when offset+LIMIT >= total', async () => {
    vi.spyOn(documentsApi, 'listDocuments').mockResolvedValue(makeListResponse([makeDoc()], 1))

    await act(async () => {
      render(<DocumentsPage />)
    })

    await waitFor(() => {
      const nextBtn = screen.getByText('Next') as HTMLButtonElement
      expect(nextBtn.disabled).toBe(true)
    })
  })

  it('enables Next button and navigates to next page', async () => {
    const firstPage = Array.from({ length: 20 }, (_, i) => makeDoc({ id: `doc-${i}`, title: `Doc ${i}` }))
    const listSpy = vi.spyOn(documentsApi, 'listDocuments')
      .mockResolvedValueOnce(makeListResponse(firstPage, 50))
      .mockResolvedValueOnce(makeListResponse([], 50))

    await act(async () => {
      render(<DocumentsPage />)
    })

    await waitFor(() => {
      const nextBtn = screen.getByText('Next') as HTMLButtonElement
      expect(nextBtn.disabled).toBe(false)
    })

    await act(async () => {
      fireEvent.click(screen.getByText('Next'))
    })

    await waitFor(() => {
      expect(listSpy).toHaveBeenCalledTimes(2)
      const secondCall = listSpy.mock.calls[1][0]
      expect(secondCall.offset).toBe(20)
    })
  })
})

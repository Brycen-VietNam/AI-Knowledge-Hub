// Task: T004 — UploadModal tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { UploadModal } from '../../src/components/UploadModal'
import * as documentsApi from '../../src/api/documentsApi'
import '../../src/i18n'

const GROUPS = [
  { id: 1, name: 'editors' },
  { id: 2, name: 'viewers' },
]

const makeFile = (name = 'report.pdf', type = 'application/pdf') =>
  new File(['content'], name, { type })

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('UploadModal', () => {
  it('renders nothing when open=false', () => {
    const { container } = render(
      <UploadModal open={false} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders modal with fields when open=true', () => {
    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)
    expect(screen.getByText(/upload document/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /upload/i })).toBeTruthy()
  })

  it('submit button is disabled when no file selected', () => {
    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)
    const submitBtn = screen.getByRole('button', { name: /upload/i })
    expect((submitBtn as HTMLButtonElement).disabled).toBe(true)
  })

  it('auto-fills title from filename stem when file selected', () => {
    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = makeFile('quarterly-report.pdf')
    fireEvent.change(fileInput, { target: { files: [file] } })
    const titleInput = screen.getByPlaceholderText(/title/i) as HTMLInputElement
    expect(titleInput.value).toBe('quarterly-report')
  })

  it('submit button is enabled after file selected', () => {
    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [makeFile()] } })
    const submitBtn = screen.getByRole('button', { name: /upload/i })
    expect((submitBtn as HTMLButtonElement).disabled).toBe(false)
  })

  it('calls uploadDocument with sourceUrl and calls onSuccess on success', async () => {
    const uploadSpy = vi.spyOn(documentsApi, 'uploadDocument').mockResolvedValue({
      doc_id: 'new-doc',
      status: 'processing',
      source_url: 'https://example.com/doc',
    })
    const onSuccess = vi.fn()
    const onClose = vi.fn()

    render(<UploadModal open={true} groups={GROUPS} onClose={onClose} onSuccess={onSuccess} />)

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [makeFile()] } })

    const urlInput = document.querySelector('input[type="url"]') as HTMLInputElement
    fireEvent.change(urlInput, { target: { value: 'https://example.com/doc' } })

    await act(async () => {
      fireEvent.submit(document.querySelector('form')!)
    })

    await waitFor(() => {
      expect(uploadSpy).toHaveBeenCalledOnce()
      expect(onSuccess).toHaveBeenCalledOnce()
      expect(onClose).toHaveBeenCalledOnce()
    })

    const [, , , , sourceUrl] = uploadSpy.mock.calls[0]
    expect(sourceUrl).toBe('https://example.com/doc')
  })

  it('shows "File too large" error on 413', async () => {
    vi.spyOn(documentsApi, 'uploadDocument').mockRejectedValue({
      response: { status: 413 },
    })

    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [makeFile()] } })

    await act(async () => {
      fireEvent.submit(document.querySelector('form')!)
    })

    await waitFor(() => {
      expect(screen.getByText('File too large')).toBeTruthy()
    })
  })

  it('shows generic error on non-413 failure', async () => {
    vi.spyOn(documentsApi, 'uploadDocument').mockRejectedValue({
      response: { status: 500 },
    })

    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [makeFile()] } })

    await act(async () => {
      fireEvent.submit(document.querySelector('form')!)
    })

    await waitFor(() => {
      expect(screen.getByText('Upload failed. Please try again.')).toBeTruthy()
    })
  })

  it('renders group options from props', () => {
    render(<UploadModal open={true} groups={GROUPS} onClose={vi.fn()} onSuccess={vi.fn()} />)
    expect(screen.getByText('editors')).toBeTruthy()
    expect(screen.getByText('viewers')).toBeTruthy()
  })

  it('calls onClose when Cancel clicked', () => {
    const onClose = vi.fn()
    render(<UploadModal open={true} groups={GROUPS} onClose={onClose} onSuccess={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })
})

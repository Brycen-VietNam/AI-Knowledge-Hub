// Task: T003 — DocumentTable tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DocumentTable } from '../../src/components/DocumentTable'
import type { DocumentItem } from '../../src/api/documentsApi'
import '../../src/i18n'

const makeDoc = (overrides: Partial<DocumentItem> = {}): DocumentItem => ({
  id: 'doc-1',
  title: 'Test Document',
  lang: 'en',
  user_group_id: 1,
  user_group_name: 'editors',
  status: 'ready',
  created_at: '2026-04-17T00:00:00',
  chunk_count: 5,
  source_url: null,
  ...overrides,
})

describe('DocumentTable', () => {
  it('renders empty state when documents array is empty', () => {
    render(<DocumentTable documents={[]} onDelete={vi.fn()} />)
    expect(screen.getByText(/no documents found/i)).toBeTruthy()
  })

  it('renders a row for each document', () => {
    const docs = [
      makeDoc({ id: 'a', title: 'Doc A' }),
      makeDoc({ id: 'b', title: 'Doc B' }),
      makeDoc({ id: 'c', title: 'Doc C' }),
    ]
    render(<DocumentTable documents={docs} onDelete={vi.fn()} />)
    expect(screen.getByText('Doc A')).toBeTruthy()
    expect(screen.getByText('Doc B')).toBeTruthy()
    expect(screen.getByText('Doc C')).toBeTruthy()
  })

  it('renders status badge with correct CSS class for ready', () => {
    const { container } = render(
      <DocumentTable documents={[makeDoc({ status: 'ready' })]} onDelete={vi.fn()} />
    )
    expect(container.querySelector('.badge-ready')).toBeTruthy()
  })

  it('renders status badge with correct CSS class for processing', () => {
    const { container } = render(
      <DocumentTable documents={[makeDoc({ status: 'processing' })]} onDelete={vi.fn()} />
    )
    expect(container.querySelector('.badge-processing')).toBeTruthy()
  })

  it('renders status badge with correct CSS class for pending', () => {
    const { container } = render(
      <DocumentTable documents={[makeDoc({ status: 'pending' })]} onDelete={vi.fn()} />
    )
    expect(container.querySelector('.badge-pending')).toBeTruthy()
  })

  it('renders status badge with correct CSS class for error', () => {
    const { container } = render(
      <DocumentTable documents={[makeDoc({ status: 'error' })]} onDelete={vi.fn()} />
    )
    expect(container.querySelector('.badge-error')).toBeTruthy()
  })

  it('calls onDelete with doc id and title when delete button clicked', () => {
    const onDelete = vi.fn()
    render(
      <DocumentTable
        documents={[makeDoc({ id: 'doc-42', title: 'My Doc' })]}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByText(/delete/i))
    expect(onDelete).toHaveBeenCalledWith('doc-42', 'My Doc')
  })

  it('shows No Group when user_group_name is absent', () => {
    render(
      <DocumentTable
        documents={[makeDoc({ user_group_name: undefined, user_group_id: null })]}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByText(/no group/i)).toBeTruthy()
  })

  it('renders source_url as a link when present', () => {
    const { container } = render(
      <DocumentTable
        documents={[makeDoc({ source_url: 'https://example.com/doc' })]}
        onDelete={vi.fn()}
      />
    )
    const link = container.querySelector('a.source-url-link') as HTMLAnchorElement
    expect(link).toBeTruthy()
    expect(link.href).toBe('https://example.com/doc')
    expect(link.target).toBe('_blank')
  })

  it('renders dash when source_url is null', () => {
    const { container } = render(
      <DocumentTable documents={[makeDoc({ source_url: null })]} onDelete={vi.fn()} />
    )
    expect(container.querySelector('.text-muted')?.textContent).toBe('—')
  })
})

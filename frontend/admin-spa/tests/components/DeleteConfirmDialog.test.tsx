// Task: T002 — DeleteConfirmDialog tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DeleteConfirmDialog } from '../../src/components/DeleteConfirmDialog'

describe('DeleteConfirmDialog', () => {
  it('renders nothing when open=false', () => {
    const { container } = render(
      <DeleteConfirmDialog
        open={false}
        title="Delete Doc"
        message="Are you sure?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders title and message when open=true', () => {
    render(
      <DeleteConfirmDialog
        open={true}
        title="Delete Document"
        message="This cannot be undone."
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )
    expect(screen.getByText('Delete Document')).toBeTruthy()
    expect(screen.getByText('This cannot be undone.')).toBeTruthy()
  })

  it('calls onConfirm when Delete button clicked', () => {
    const onConfirm = vi.fn()
    const { container } = render(
      <DeleteConfirmDialog
        open={true}
        title="Delete"
        message="Sure?"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    )
    fireEvent.click(container.querySelector('.btn-danger')!)
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when Cancel button clicked', () => {
    const onCancel = vi.fn()
    render(
      <DeleteConfirmDialog
        open={true}
        title="Delete"
        message="Sure?"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    )
    fireEvent.click(screen.getByText('Cancel'))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('calls onCancel when overlay clicked', () => {
    const onCancel = vi.fn()
    const { container } = render(
      <DeleteConfirmDialog
        open={true}
        title="Delete"
        message="Sure?"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    )
    const overlay = container.querySelector('.confirm-dialog-overlay')!
    fireEvent.click(overlay)
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('does not call onCancel when dialog body clicked (stopPropagation)', () => {
    const onCancel = vi.fn()
    const { container } = render(
      <DeleteConfirmDialog
        open={true}
        title="Delete"
        message="Sure?"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    )
    const dialog = container.querySelector('.confirm-dialog')!
    fireEvent.click(dialog)
    expect(onCancel).not.toHaveBeenCalled()
  })
})

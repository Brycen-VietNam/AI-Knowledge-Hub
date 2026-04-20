// Task: T002 — GroupFormModal tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { GroupFormModal } from '../../src/components/GroupFormModal'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

const INITIAL_GROUP: adminApi.GroupItem = {
  id: 1,
  name: 'editors',
  is_admin: false,
  member_count: 3,
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('GroupFormModal', () => {
  it('renders empty name field in create mode', () => {
    render(<GroupFormModal mode="create" onSave={vi.fn()} onClose={vi.fn()} />)
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    expect(nameInput.value).toBe('')
  })

  it('renders initial values in edit mode', () => {
    render(
      <GroupFormModal mode="edit" initial={INITIAL_GROUP} onSave={vi.fn()} onClose={vi.fn()} />
    )
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    const checkbox = document.querySelector('input[type="checkbox"]') as HTMLInputElement
    expect(nameInput.value).toBe('editors')
    expect(checkbox.checked).toBe(false)
  })

  it('shows error inline when name is empty on submit', async () => {
    render(<GroupFormModal mode="create" onSave={vi.fn()} onClose={vi.fn()} />)
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.upload-error')).toBeTruthy()
    })
  })

  it('shows error inline when name exceeds 100 chars', async () => {
    render(<GroupFormModal mode="create" onSave={vi.fn()} onClose={vi.fn()} />)
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    fireEvent.change(nameInput, { target: { value: 'a'.repeat(101) } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.upload-error')).toBeTruthy()
    })
  })

  it('calls createGroup and onSave+onClose on success in create mode', async () => {
    const newGroup = { id: 2, name: 'writers', is_admin: false, member_count: 0 }
    vi.spyOn(adminApi, 'createGroup').mockResolvedValue(newGroup)
    const onSave = vi.fn()
    const onClose = vi.fn()
    render(<GroupFormModal mode="create" onSave={onSave} onClose={onClose} />)
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    fireEvent.change(nameInput, { target: { value: 'writers' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(adminApi.createGroup).toHaveBeenCalledWith('writers', false)
      expect(onSave).toHaveBeenCalledWith('writers', false)
      expect(onClose).toHaveBeenCalledOnce()
    })
  })

  it('calls updateGroup and onSave+onClose on success in edit mode', async () => {
    const updated = { ...INITIAL_GROUP, name: 'senior-editors' }
    vi.spyOn(adminApi, 'updateGroup').mockResolvedValue(updated)
    const onSave = vi.fn()
    const onClose = vi.fn()
    render(
      <GroupFormModal mode="edit" initial={INITIAL_GROUP} onSave={onSave} onClose={onClose} />
    )
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    fireEvent.change(nameInput, { target: { value: 'senior-editors' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(adminApi.updateGroup).toHaveBeenCalledWith(1, 'senior-editors', false)
      expect(onSave).toHaveBeenCalledWith('senior-editors', false)
      expect(onClose).toHaveBeenCalledOnce()
    })
  })

  it('shows inline error on API failure', async () => {
    vi.spyOn(adminApi, 'createGroup').mockRejectedValue(new Error('network'))
    render(<GroupFormModal mode="create" onSave={vi.fn()} onClose={vi.fn()} />)
    const nameInput = document.querySelector('input[type="text"]') as HTMLInputElement
    fireEvent.change(nameInput, { target: { value: 'newgroup' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.upload-error')).toBeTruthy()
    })
  })

  it('calls onClose when cancel button is clicked', () => {
    const onClose = vi.fn()
    render(<GroupFormModal mode="create" onSave={vi.fn()} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })
})

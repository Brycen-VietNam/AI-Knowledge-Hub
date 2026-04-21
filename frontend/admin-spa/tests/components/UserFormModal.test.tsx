// Task: S006 T004 — UserFormModal full AC coverage
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UserFormModal } from '../../src/components/UserFormModal'
import * as adminApi from '../../src/api/adminApi'
import '../../src/i18n'

const GROUPS: adminApi.GroupItem[] = [
  { id: 1, name: 'editors', is_admin: false, member_count: 3 },
  { id: 2, name: 'viewers', is_admin: false, member_count: 5 },
]

const CREATED_USER: adminApi.UserItem = {
  id: 'u99',
  email: 'newuser@example.com',
  is_active: true,
  groups: [],
}

beforeEach(() => {
  vi.restoreAllMocks()
})

function fillRequiredFields(sub = 'newuser', password = 'Str0ngPassword!') {
  const subInput = document.querySelector('input[pattern]') as HTMLInputElement
  fireEvent.change(subInput, { target: { value: sub } })
  const pwInputs = document.querySelectorAll('input[type="password"]')
  // The password input (type=password by default)
  const pwInput = pwInputs[0] as HTMLInputElement
  fireEvent.change(pwInput, { target: { value: password } })
}

describe('UserFormModal', () => {
  it('renders all required fields: sub, email, display_name, password, group checkboxes', () => {
    render(<UserFormModal onSave={vi.fn()} onClose={vi.fn()} groups={GROUPS} />)
    // sub field — has pattern attribute
    expect(document.querySelector('input[pattern]')).toBeTruthy()
    // email field
    expect(document.querySelector('input[type="email"]')).toBeTruthy()
    // password field (hidden by default)
    expect(document.querySelector('input[type="password"]')).toBeTruthy()
    // group checkboxes
    expect(document.querySelectorAll('input[type="checkbox"]').length).toBe(2)
    expect(screen.getByText('editors')).toBeTruthy()
    expect(screen.getByText('viewers')).toBeTruthy()
  })

  it('submit button disabled while isSubmitting', async () => {
    let resolveCreate!: (v: adminApi.UserItem) => void
    vi.spyOn(adminApi, 'createUser').mockReturnValue(
      new Promise<adminApi.UserItem>((res) => { resolveCreate = res }),
    )
    render(<UserFormModal onSave={vi.fn()} onClose={vi.fn()} groups={[]} />)
    fillRequiredFields()
    const submitBtn = document.querySelector('button[type="submit"]') as HTMLButtonElement
    expect(submitBtn.disabled).toBe(false)
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => expect(submitBtn.disabled).toBe(true))
    resolveCreate(CREATED_USER)
  })

  it('generate password fills the password field and reveals it', () => {
    render(<UserFormModal onSave={vi.fn()} onClose={vi.fn()} groups={[]} />)
    // Password hidden by default
    expect(document.querySelector('input[type="password"]')).toBeTruthy()
    expect(document.querySelector('input[type="text"][minlength]')).toBeNull()
    // Click generate
    const generateBtn = screen.getByText('Generate')
    fireEvent.click(generateBtn)
    // Password field now revealed (type="text") and has value
    const pwInput = document.querySelector('input[minlength="12"]') as HTMLInputElement
    expect(pwInput).toBeTruthy()
    expect(pwInput.value.length).toBe(16)
    expect(pwInput.type).toBe('text')
  })

  it('show/hide toggle switches password field type', () => {
    render(<UserFormModal onSave={vi.fn()} onClose={vi.fn()} groups={[]} />)
    expect(document.querySelector('input[type="password"]')).toBeTruthy()
    const showBtn = screen.getByText('Show')
    fireEvent.click(showBtn)
    expect(document.querySelector('input[type="password"]')).toBeNull()
    expect(document.querySelector('input[minlength="12"]')).toBeTruthy()
    const hideBtn = screen.getByText('Hide')
    fireEvent.click(hideBtn)
    expect(document.querySelector('input[type="password"]')).toBeTruthy()
  })

  it('409 shows inline error, modal stays open', async () => {
    const axiosErr = { response: { status: 409 } }
    vi.spyOn(adminApi, 'createUser').mockRejectedValue(axiosErr)
    const onClose = vi.fn()
    render(<UserFormModal onSave={vi.fn()} onClose={onClose} groups={[]} />)
    fillRequiredFields()
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.form-error')).toBeTruthy()
      // Modal still in DOM
      expect(document.querySelector('.upload-modal')).toBeTruthy()
    })
    expect(onClose).not.toHaveBeenCalled()
  })

  it('422 shows server message, modal stays open', async () => {
    const axiosErr = {
      response: { status: 422, data: { detail: 'sub must be unique per tenant' } },
    }
    vi.spyOn(adminApi, 'createUser').mockRejectedValue(axiosErr)
    const onClose = vi.fn()
    render(<UserFormModal onSave={vi.fn()} onClose={onClose} groups={[]} />)
    fillRequiredFields()
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      const errEl = document.querySelector('.form-error')
      expect(errEl).toBeTruthy()
      expect(errEl!.textContent).toBe('sub must be unique per tenant')
    })
    expect(onClose).not.toHaveBeenCalled()
  })

  it('unexpected error shows generic message, modal stays open', async () => {
    vi.spyOn(adminApi, 'createUser').mockRejectedValue(new Error('Network Error'))
    const onClose = vi.fn()
    render(<UserFormModal onSave={vi.fn()} onClose={onClose} groups={[]} />)
    fillRequiredFields()
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(document.querySelector('.form-error')).toBeTruthy()
    })
    expect(onClose).not.toHaveBeenCalled()
  })

  it('success calls onSave with returned user and onClose', async () => {
    vi.spyOn(adminApi, 'createUser').mockResolvedValue(CREATED_USER)
    const onSave = vi.fn()
    const onClose = vi.fn()
    render(<UserFormModal onSave={onSave} onClose={onClose} groups={[]} />)
    fillRequiredFields()
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(CREATED_USER)
      expect(onClose).toHaveBeenCalledOnce()
    })
  })

  it('error is cleared when user resubmits', async () => {
    const axiosErr = { response: { status: 409 } }
    vi.spyOn(adminApi, 'createUser')
      .mockRejectedValueOnce(axiosErr)
      .mockResolvedValueOnce(CREATED_USER)
    const onSave = vi.fn()
    render(<UserFormModal onSave={onSave} onClose={vi.fn()} groups={[]} />)
    fillRequiredFields()
    // First submit → 409 error
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => expect(document.querySelector('.form-error')).toBeTruthy())
    // Second submit → success → error cleared
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce())
    expect(document.querySelector('.form-error')).toBeNull()
  })

  it('i18n: labels use t() — rendered text matches locale strings', () => {
    render(<UserFormModal onSave={vi.fn()} onClose={vi.fn()} groups={[]} />)
    // en locale expected strings
    expect(screen.getByText('Create User')).toBeTruthy()
    expect(screen.getByText('Username')).toBeTruthy()
    expect(screen.getByText('Password')).toBeTruthy()
    expect(screen.getByText('Save')).toBeTruthy()
    expect(screen.getByText('Cancel')).toBeTruthy()
  })

  it('selected group_ids are number[] — sends correct type to createUser', async () => {
    const spy = vi.spyOn(adminApi, 'createUser').mockResolvedValue(CREATED_USER)
    render(<UserFormModal onSave={vi.fn()} onClose={vi.fn()} groups={GROUPS} />)
    fillRequiredFields()
    // Select group 1
    const checkboxes = document.querySelectorAll('input[type="checkbox"]')
    fireEvent.click(checkboxes[0]) // editors (id=1)
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => expect(spy).toHaveBeenCalled())
    const payload = spy.mock.calls[0][0]
    expect(payload.group_ids).toEqual([1])
    expect(typeof payload.group_ids![0]).toBe('number')
  })
})

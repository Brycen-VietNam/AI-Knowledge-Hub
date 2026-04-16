import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchInput } from '../../../src/components/query/SearchInput'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === 'search.char_count') return `${opts?.count}/512`
      if (key === 'search.placeholder') return 'Search knowledge base...'
      if (key === 'search.button') return 'Search'
      return key
    },
  }),
}))

function renderInput(props: Partial<Parameters<typeof SearchInput>[0]> = {}) {
  const defaults = {
    value: '',
    onChange: vi.fn(),
    onSubmit: vi.fn(),
    isLoading: false,
  }
  return render(<SearchInput {...defaults} {...props} />)
}

describe('SearchInput — renders', () => {
  it('renders textarea and button', () => {
    renderInput()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument()
  })

  it('shows char counter', () => {
    renderInput({ value: 'hello' })
    expect(screen.getByText('5/512')).toBeInTheDocument()
  })
})

describe('SearchInput — submit disabled when empty', () => {
  it('button disabled when value is empty string', () => {
    renderInput({ value: '' })
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('button disabled when value is whitespace only', () => {
    renderInput({ value: '   ' })
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('button enabled when value has content', () => {
    renderInput({ value: 'some query' })
    expect(screen.getByRole('button')).not.toBeDisabled()
  })
})

describe('SearchInput — 512-char limit', () => {
  it('button disabled when value exceeds 512 chars', () => {
    renderInput({ value: 'a'.repeat(513) })
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('button enabled at exactly 512 chars', () => {
    renderInput({ value: 'a'.repeat(512) })
    expect(screen.getByRole('button')).not.toBeDisabled()
  })
})

describe('SearchInput — isLoading disables both', () => {
  it('textarea disabled when isLoading', () => {
    renderInput({ value: 'query', isLoading: true })
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('button disabled when isLoading', () => {
    renderInput({ value: 'query', isLoading: true })
    expect(screen.getByRole('button')).toBeDisabled()
  })
})

describe('SearchInput — IME guard', () => {
  it('does not call onSubmit on Enter during IME composition', () => {
    const onSubmit = vi.fn()
    renderInput({ value: 'テスト', onSubmit })
    const textarea = screen.getByRole('textbox')
    // jsdom does not set isComposing via compositionStart; dispatch native KeyboardEvent directly
    const evt = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, isComposing: true })
    textarea.dispatchEvent(evt)
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit on Enter when not composing', () => {
    const onSubmit = vi.fn()
    renderInput({ value: 'query text', onSubmit })
    const textarea = screen.getByRole('textbox')
    // isComposing defaults to false
    const evt = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, isComposing: false })
    textarea.dispatchEvent(evt)
    expect(onSubmit).toHaveBeenCalledTimes(1)
  })

  it('does not submit on Shift+Enter', () => {
    const onSubmit = vi.fn()
    renderInput({ value: 'query text', onSubmit })
    const textarea = screen.getByRole('textbox')
    const evt = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true, bubbles: true, isComposing: false })
    textarea.dispatchEvent(evt)
    expect(onSubmit).not.toHaveBeenCalled()
  })
})

describe('SearchInput — onChange', () => {
  it('calls onChange when user types', async () => {
    const onChange = vi.fn()
    renderInput({ value: '', onChange })
    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'hello')
    expect(onChange).toHaveBeenCalled()
  })
})

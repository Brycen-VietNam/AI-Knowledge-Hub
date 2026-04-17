import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LanguageSelector } from '../../src/components/LanguageSelector'
import i18n from '../../src/i18n'
import '../../src/i18n'

describe('LanguageSelector', () => {
  it('renders 4 language options', () => {
    render(<LanguageSelector />)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(4)
  })

  it('changes language on selection', async () => {
    render(<LanguageSelector />)
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'ja')
    expect(i18n.language).toBe('ja')
  })

  it('has aria-label attribute', () => {
    render(<LanguageSelector />)
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-label')
  })
})

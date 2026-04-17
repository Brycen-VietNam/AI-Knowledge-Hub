import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LanguageSelector } from '../../../src/components/query/LanguageSelector'

// vi.hoisted ensures these run before vi.mock factories (which are hoisted to top of file)
const { mockChangeLanguage } = vi.hoisted(() => ({
  mockChangeLanguage: vi.fn(),
}))

// Mock react-i18next (must include initReactI18next — used by i18n/index.ts at load time)
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      if (key === 'lang.selector_label') return 'Language'
      return key
    },
  }),
  initReactI18next: { type: '3rdParty', init: vi.fn() },
}))

vi.mock('../../../src/i18n', () => ({
  default: {
    language: 'en',
    changeLanguage: mockChangeLanguage,
  },
}))

beforeEach(() => {
  mockChangeLanguage.mockClear()
  localStorage.clear()
})

describe('LanguageSelector — renders', () => {
  it('renders a select element', () => {
    render(<LanguageSelector />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('renders all 4 language options', () => {
    render(<LanguageSelector />)
    expect(screen.getByRole('option', { name: '日本語' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'English' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Tiếng Việt' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '한국어' })).toBeInTheDocument()
  })

  it('shows selector label', () => {
    render(<LanguageSelector />)
    expect(screen.getByLabelText('Language')).toBeInTheDocument()
  })
})

describe('LanguageSelector — onChange', () => {
  it('calls i18n.changeLanguage with selected value', () => {
    render(<LanguageSelector />)
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'ja' } })
    expect(mockChangeLanguage).toHaveBeenCalledWith('ja')
  })

  it('persists selected lang to localStorage', () => {
    render(<LanguageSelector />)
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'vi' } })
    expect(localStorage.getItem('lang')).toBe('vi')
  })

  it('fires both changeLanguage and localStorage on change', () => {
    render(<LanguageSelector />)
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'ko' } })
    expect(mockChangeLanguage).toHaveBeenCalledWith('ko')
    expect(localStorage.getItem('lang')).toBe('ko')
  })
})

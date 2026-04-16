import { describe, it, expect, beforeAll } from 'vitest'
import i18n from '../../src/i18n'

const REQUIRED_KEYS = [
  'app.title',
  'login.username',
  'login.password',
  'login.submit',
  'login.error_invalid',
  'login.error_unavailable',
  'login.session_expired',
  // S002 keys
  'search.placeholder',
  'search.button',
  'lang.selector_label',
  // S003 keys
  'results.no_results',
  'results.low_confidence_warning',
  'results.show_more',
  'results.hide',
  'results.error_rate_limit',
  'results.error_service',
  'results.no_source_warning',
]

const LOCALES = ['en', 'ja', 'vi', 'ko'] as const

beforeAll(async () => {
  await i18n.changeLanguage('en')
})

describe('i18n — all required keys present in all locales', () => {
  for (const locale of LOCALES) {
    for (const key of REQUIRED_KEYS) {
      it(`${locale}: "${key}" is defined`, () => {
        const val = i18n.getFixedT(locale)(key)
        expect(val).toBeTruthy()
        expect(val).not.toBe(key) // key should resolve, not return itself
      })
    }
  }
})

describe('i18n — language switching', () => {
  it('switches to Japanese', async () => {
    await i18n.changeLanguage('ja')
    expect(i18n.t('login.submit')).toBe('サインイン')
  })

  it('switches to Vietnamese', async () => {
    await i18n.changeLanguage('vi')
    expect(i18n.t('login.submit')).toBe('Đăng nhập')
  })

  it('switches to Korean', async () => {
    await i18n.changeLanguage('ko')
    expect(i18n.t('login.submit')).toBe('로그인')
  })

  it('falls back to English', async () => {
    await i18n.changeLanguage('en')
    expect(i18n.t('login.submit')).toBe('Sign In')
  })
})

describe('i18n — localStorage stores lang (not token)', () => {
  it('localStorage lang key is allowed', () => {
    localStorage.setItem('lang', 'en')
    expect(localStorage.getItem('lang')).toBe('en')
  })

  it('localStorage token key is never set by i18n', () => {
    expect(localStorage.getItem('token')).toBeNull()
  })
})

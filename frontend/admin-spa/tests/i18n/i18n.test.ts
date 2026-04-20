import { describe, it, expect } from 'vitest'
import i18n from '../../src/i18n'

describe('i18n', () => {
  it('fallback language is en', () => {
    expect(i18n.options.fallbackLng).toEqual(['en'])
  })

  it('t(login.access_denied) returns correct string in en', async () => {
    await i18n.changeLanguage('en')
    expect(i18n.t('login.access_denied')).toBe('Access denied. Admin privileges required.')
  })

  it('t(login.session_expired) returns correct string in ja', async () => {
    await i18n.changeLanguage('ja')
    expect(i18n.t('login.session_expired')).toBe('セッションが期限切れです。再度サインインしてください。')
  })

  it('localStorage key is admin-spa-lang', () => {
    const detection = i18n.options.detection as { lookupLocalStorage?: string }
    expect(detection.lookupLocalStorage).toBe('admin-spa-lang')
  })

  it('supported languages include all 4 locales', () => {
    expect(i18n.options.supportedLngs).toContain('en')
    expect(i18n.options.supportedLngs).toContain('ja')
    expect(i18n.options.supportedLngs).toContain('vi')
    expect(i18n.options.supportedLngs).toContain('ko')
  })
})

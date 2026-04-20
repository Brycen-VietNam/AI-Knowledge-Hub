// Spec: docs/admin-spa/spec/admin-spa.spec.md
// Task: T004 — i18n init — 4 locales; lookupLocalStorage: 'admin-spa-lang' (no collision with frontend-spa)
import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import ja from './locales/ja.json'
import vi from './locales/vi.json'
import ko from './locales/ko.json'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ja: { translation: ja },
      vi: { translation: vi },
      ko: { translation: ko },
    },
    supportedLngs: ['en', 'ja', 'vi', 'ko'],
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'admin-spa-lang',
      caches: ['localStorage'],
    },
  })

export default i18n

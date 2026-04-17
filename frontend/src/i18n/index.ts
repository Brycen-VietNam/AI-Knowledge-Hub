// Spec: docs/frontend-spa/spec/frontend-spa.spec.md
// Task: T006 — i18n init — 4 locales; Decision: D003 — lang in localStorage, token NEVER
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
      lookupLocalStorage: 'lang',
      caches: ['localStorage'],
    },
  })

export default i18n

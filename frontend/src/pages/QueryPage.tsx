// Spec: docs/frontend-spa/spec/frontend-spa.spec.md#S002
// Task: T006 (S003) — QueryPage — wire AnswerPanel + submitQuery
// Task: T005 (S004) — add HistoryPanel sidebar
// Task: S002/T003 — replace inline styles with app-body grid; LanguageSelector moved to App header
// Decision: D004 — query history session-only; D002 — token never in localStorage
import { useQueryStore } from '../store/queryStore'
import { SearchInput } from '../components/query/SearchInput'
import { AnswerPanel } from '../components/results/AnswerPanel'
import { HistoryPanel } from '../components/history/HistoryPanel'
import i18n from '../i18n'

export function QueryPage() {
  const { query, isLoading, error, result, setQuery, submitQuery } = useQueryStore()

  function handleSubmit() {
    const lang = i18n.language?.split('-')[0] ?? 'en'
    void submitQuery(query, lang)
  }

  return (
    <div className="app-body">
      <main>
        <SearchInput
          value={query}
          onChange={setQuery}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
        <AnswerPanel
          answer={result?.answer ?? ''}
          citations={result?.citations ?? []}
          confidence={result?.confidence ?? 0}
          isLoading={isLoading}
          error={error}
        />
      </main>
      <HistoryPanel />
    </div>
  )
}

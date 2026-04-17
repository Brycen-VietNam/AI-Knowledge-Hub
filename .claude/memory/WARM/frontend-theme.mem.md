# WARM Memory: frontend-theme
Spec: `docs/frontend-theme/spec/frontend-theme.spec.md`
Updated: 2026-04-17 | Status: CLARIFIED

---

## Feature Summary
**Goal**: Apply design theme from `docs/knowledge-hub.html` reference to React/Vite SPA.
**Scope**: 5 stories — design tokens → header → search → results → login + panels.
**Impact**: Visual launch unblocking; currently SPA is unstyled.
**Blockers**: None. Depends on frontend-spa (S001–S005 done).

---

## Key Decisions
| Decision | Rationale | Owner |
|----------|-----------|-------|
| **D001** — CSS variables (no Tailwind) | Simplicity, no new deps, knowledge-hub.html already defines tokens in CSS | Claude |
| **D002** — Single light theme | Desktop-first MVP; dark mode post-launch | Claude |
| **D003** — index.css (not tokens.css) | Vite convention, single global CSS import | User |
| **D004** — DM Sans / DM Mono / Playfair | Font family from knowledge-hub.html reference | Claude |
| **D005** — Header on all pages; user pill hidden on LoginPage | Header always visible; user pill conditional on `token !== null` | User |
| **D006** — Logo: "Knowledge Hub" + "BRYSEN GROUP" | Confirmed from knowledge-hub.html reference | User |
| **D007** — Global CSS classes in index.css (no modules, no inline style) | Single file, supports pseudo-states, consistent with design reference approach | User |

---

## Tech Stack
- CSS: Plain CSS variables (no preprocessor)
- Fonts: Google Fonts (async, non-blocking)
- Components: Existing React components from frontend-spa S001–S005
- Tests: Existing 208 tests (styling visual only, no logic change expected)

---

## File Manifest (TOUCH list)
**Create:**
- `frontend/src/index.css` — design tokens + fonts + body reset

**Modify:**
- `frontend/src/main.tsx` — import index.css
- `frontend/src/App.tsx` — header markup + grid shell
- `frontend/src/pages/QueryPage.tsx` — grid layout
- `frontend/src/pages/LoginPage.tsx` — card + brand strip
- `frontend/src/components/query/SearchInput.tsx` — search panel card
- `frontend/src/components/query/LanguageSelector.tsx` — inline pill
- `frontend/src/components/results/AnswerPanel.tsx` — remove Tailwind classNames
- `frontend/src/components/results/ConfidenceBadge.tsx` — remove Tailwind, use CSS vars
- `frontend/src/components/results/LowConfidenceWarning.tsx` — remove Tailwind, use CSS vars
- `frontend/src/components/results/CitationList.tsx` — remove Tailwind, use CSS vars
- `frontend/src/components/results/CitationItem.tsx` — remove Tailwind, use CSS vars
- `frontend/src/components/history/HistoryPanel.tsx` — aside card styling
- `frontend/src/components/history/HistoryItem.tsx` — row with hover, DM Mono timestamp
- `frontend/src/components/auth/LoginForm.tsx` — input + button styling

**Design Reference:**
- `docs/knowledge-hub.html` — CSS tokens (lines 11–37), header (lines 50–119), layout (lines 121–128)
- `docs/knowledge-hub.png` — visual screenshot

---

## Story Status Table

| Story | Title | Status | AC Count | Notes | Tasks |
|-------|-------|--------|----------|-------|-------|
| S001 | Design tokens + global CSS baseline | ✅ DONE | 8 | All 208 tests pass, build clean, CSS tokens defined | T001✅, T002✅ |
| S002 | Header + app shell layout | ✅ DONE | 10 | 208/208 tests pass, build clean (2.06s) | T001✅, T002✅, T003✅ |
| S003 | Search area + LanguageSelector | ✅ DONE | 8 | 208/208 tests pass, build clean | T001✅, T002✅, T003✅ |
| S004 | Results area styling (Confidence, Citations) | ✅ DONE | 12 | 208/208 tests pass | T001✅, T002✅, T003✅, T004✅ |
| S005 | Login page + HistoryPanel + HistoryItem | ✅ DONE | 8 | 208/208 tests pass, build 1.95s | T001✅, T002✅, T003✅ |

**Total ACs**: 48  
**Test suite**: 208 tests (all must pass after styling)

---

## Open Questions
1. Should login page also have a link to "sign up" or "forgot password"? → Out of scope (S005 AC only mentions login flow)
2. Should HistoryPanel be sticky? → Per design reference, only header sticky; panel scrolls with content
3. Mobile breakpoint? → Out of scope (desktop-first MVP)

---

## Next Actions
1. `/tasks frontend-theme S001` — first task definition, then implement sequentially
2. Implement stories S001–S005 sequentially (design tokens → header → search → results → login)
3. `/report frontend-theme` — finalize with all ACs traced, commit, merge to main

---

## Sync: 2026-04-17 Session #075
**Decisions added**: D001 (CSS vars), D002 (single light theme), D003 (index.css)
**Files created**: spec.md, sources.md, WARM memory
**Status**: /specify DONE, /clarify → /plan → /tasks flow ready
**Blockers**: None

## Sync: 2026-04-17 Session #076
**Decisions added**: D005 (header all pages, user pill conditional), D006 (logo text confirmed), D007 (global CSS in index.css)
**Files modified**: spec.md (S002 AC1/AC3/AC4 + impl notes), clarify.md (4 blockers → RESOLVED)
**Files created**: `docs/frontend-theme/clarify/frontend-theme.clarify.md`
**Questions resolved**: Q1–Q4 (all blockers), Q7 (AC7 count corrected to 16 tests)
**Status**: /clarify DONE → next: /checklist → /plan
**Blockers**: None

## Sync: 2026-04-17 Session #077
**Checklist**: ✅ PASS — 30/30 items (all spec quality, arch alignment, agent readiness checks)
**Plan**: ✅ GENERATED — 5 stories, sequential critical path (S001→S005), 1 session, ~12k tokens total
**Files created**: `docs/frontend-theme/reviews/checklist.md`, `docs/frontend-theme/plan/frontend-theme.plan.md`
**Status**: /plan DONE → next: /tasks frontend-theme S001 → implement S001–S005 sequentially
**Blockers**: None

## Sync: 2026-04-17 Session #078 (final)
**Tasks**: S005 T001✅ T002✅ T003✅ (S005 DONE)
**S005 Complete**: Login page + HistoryPanel + HistoryItem styling
**Files created**: `docs/frontend-theme/tasks/S005.tasks.md`
**Files modified**: `frontend/src/index.css` (login + history CSS ~170 lines), `frontend/src/pages/LoginPage.tsx` (login-page/login-card/brand strip), `frontend/src/components/auth/LoginForm.tsx` (form-input/btn-primary), `frontend/src/components/history/HistoryPanel.tsx` (history-panel/header/list), `frontend/src/components/history/HistoryItem.tsx` (history-item/bullet/content)
**Build & Test**: npm run test ✅ (208/208 pass), npm run build ✅ (1.95s, CSS 11.58 KB)
**Status**: ALL 5 STORIES DONE → next: /report frontend-theme
**Blockers**: None

---

## Design Reference Details
**Color Palette** (from knowledge-hub.html `:root`):
- Primary: `--indigo: #6366f1`, `--indigo-dark: #4f46e5`, `--indigo-light: #eef2ff`
- Surfaces: `--bg: #f0f2f7` (page), `--surface: #ffffff` (card), `--surface-2: #f7f8fc` (header)
- Confidence: `--emerald: #10b981` (high), `--amber: #f59e0b` (medium), `--red: #ef4444` (low)
- Text: `--text: #1a1d2e` (primary), `--text-2: #5b6178` (secondary), `--text-3: #9198b5` (tertiary)

**Typography**:
- Body: DM Sans (400, 5–600 weights)
- Monospace (score, timestamp): DM Mono (400, 500)
- Heading (logo, title): Playfair Display (700)

**Header**:
- Gradient: `linear-gradient(135deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%)`
- Height: `60px` (`--header-h`)
- Shadow: Inigo-tinted at `0 2px 16px rgba(67,56,202,.35)`

---

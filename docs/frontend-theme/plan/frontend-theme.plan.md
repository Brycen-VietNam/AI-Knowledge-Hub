# Plan: frontend-theme
Generated: 2026-04-17 | Checklist: ✅ PASS

---

## LAYER 1 — Plan Summary

| Field | Value |
|-------|-------|
| **Feature** | frontend-theme |
| **Stories** | 5 (S001–S005) |
| **Total ACs** | 48 |
| **Total files** | 14 (1 new, 13 modified) |
| **Critical path** | S001 → S002 → S003 → S004 → S005 |
| **Parallel groups** | None (sequential design system build) |
| **Sessions estimated** | 1 (all stories in one feature-branch session) |
| **Token budget total** | ~12k tokens |
| **Agent** | frontend-agent (haiku) |
| **Model** | claude-haiku-4-5-20251001 |

### Execution Strategy
```
S001: Design tokens + global CSS baseline (2.4k tokens)
  └─→ S002: Header + app shell layout (2.4k tokens)
      └─→ S003: Search area + LanguageSelector styling (2.4k tokens)
          └─→ S004: Results area styling (2.4k tokens)
              └─→ S005: Login page + HistoryPanel styling (2.4k tokens)
```

**Why sequential**: Each story builds on previous tokens/layout/components. S001 establishes CSS variables (tokens) that S002–S005 reference. Header (S002) must exist before search/results layout. Results styling (S004) depends on search styling (S003).

---

## LAYER 2 — Per-Story Plans

### S001: Design tokens + global CSS baseline

**Story**: As a frontend developer, I want a single CSS file with all design tokens extracted from knowledge-hub.html, so that components can reference `var(--indigo)` instead of hardcoded hex values.

| Field | Value |
|-------|-------|
| **Agent** | frontend-agent |
| **Depends on** | None |
| **Parallelizable** | N/A (first in chain) |
| **Files created** | `frontend/src/index.css` |
| **Files modified** | `frontend/src/main.tsx` (import index.css) |
| **ACs** | 8 |
| **Est. tokens** | 2.4k |
| **Test command** | `npm run build && npm run test` (full suite) |
| **Definition** | Copy `:root` CSS variables (colors, shadows, radii, header-h), Google Fonts `@import` (DM Sans, DM Mono, Playfair Display), body reset from knowledge-hub.html lines 8–48. Ensure `npm run build` passes with zero TS errors. Visual check: page background matches `--bg = #f0f2f7`, text matches `--text = #1a1d2e`. |

**Key ACs**:
- AC1: index.css created and imported in main.tsx (before React root)
- AC2–AC3: ≥20 design tokens in `:root` (colors, shadows, radii, header-h = 60px)
- AC4: Google Fonts @import loads DM Sans/DM Mono/Playfair synchronously
- AC5–AC6: Body global reset applied (font-family, background, color, box-sizing reset)
- AC7–AC8: Build passes, visual check matches reference

**Subagent dispatch**: Self-contained (haiku, single file creation + one import modification).

---

### S002: Header + app shell layout

**Story**: As a user/stakeholder, I want a sticky header with Brysen Group branding (logo, gradient background, user pill) and a grid-based app shell, so that the app looks professional and content has proper spacing.

| Field | Value |
|-------|-------|
| **Agent** | frontend-agent |
| **Depends on** | S001 (CSS tokens) |
| **Parallelizable** | No |
| **Files modified** | `frontend/src/App.tsx`, `frontend/src/pages/QueryPage.tsx` |
| **ACs** | 10 |
| **Est. tokens** | 2.4k |
| **Test command** | `npm run test` (208 tests, all must pass) |
| **Definition** | Add `<header>` component to App.tsx (sticky, z-index 100, height 60px, indigo gradient). Header includes logo icon + text ("Knowledge Hub" / "BRYSEN GROUP" in Playfair Display), user pill (avatar + username from useAuthStore(), hidden on LoginPage when token === null), language selector. Below header, add grid layout: `grid-template-columns: 1fr 280px; gap: 20px; max-width: 1280px`. Left column: search + results. Right column: HistoryPanel (280px fixed). |

**Key ACs**:
- AC1–AC2: Sticky header, exact gradient `linear-gradient(135deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%)`
- AC3–AC5: Logo icon + text, user pill (conditional), language selector
- AC6–AC7: Grid layout 1fr + 280px, HistoryPanel in right column
- AC8–AC10: Visual parity with reference, tests pass (208 green), build clean

**Subagent dispatch**: Self-contained (header markup + grid CSS modification in 2 files).

---

### S003: Search area + LanguageSelector styling

**Story**: As a user, I want a visually polished search card with proper input styling, character count badge, and inline language selector, so that searching feels responsive and modern.

| Field | Value |
|-------|-------|
| **Agent** | frontend-agent |
| **Depends on** | S002 (header layout established) |
| **Parallelizable** | No |
| **Files modified** | `frontend/src/components/query/SearchInput.tsx`, `frontend/src/components/query/LanguageSelector.tsx` |
| **ACs** | 8 |
| **Est. tokens** | 2.4k |
| **Test command** | `npm run test -- tests/components/query/` |
| **Definition** | Apply CSS to search components: `.search-panel` card with surface background, border, shadow, border-radius. Textarea input: border, border-radius, `:focus` ring (indigo). Submit button: indigo gradient with hover darkening. Character count badge: DM Mono, right-aligned. Language selector pill: transparent white background, indigo-light text. Reference knowledge-hub.html lines 130–200. |

**Key ACs**:
- AC1–AC3: Search panel card styling (surface, border, shadow, border-radius)
- AC4–AC5: Submit button gradient, character count badge
- AC6: Language selector pill styling
- AC7–AC8: Visual parity, tests pass

**Subagent dispatch**: Self-contained (CSS classes in 2 existing components).

---

### S004: Results area styling (AnswerPanel, ConfidenceBadge, Citations)

**Story**: As a user, I want results (answer, confidence, citations) displayed with proper color coding and card styling, so that I can quickly see answer confidence and source documents with visual hierarchy.

| Field | Value |
|-------|-------|
| **Agent** | frontend-agent |
| **Depends on** | S003 (search layout established) |
| **Parallelizable** | No |
| **Files modified** | `frontend/src/components/results/AnswerPanel.tsx`, `frontend/src/components/results/ConfidenceBadge.tsx`, `frontend/src/components/results/LowConfidenceWarning.tsx`, `frontend/src/components/results/CitationList.tsx`, `frontend/src/components/results/CitationItem.tsx` |
| **ACs** | 12 |
| **Est. tokens** | 2.4k |
| **Test command** | `npm run test -- tests/components/results/` |
| **Definition** | Remove non-functional Tailwind classNames from 5 result components. Replace with CSS classes in `frontend/src/index.css`: ConfidenceBadge (emerald HIGH / amber MEDIUM / red LOW variants), AnswerPanel card, LowConfidenceWarning alert, CitationList + CitationItem cards. Use CSS variables (--emerald, --emerald-light, --amber, --amber-light, --red, --red-light, --text, --text-3, --surface, --surface-2, --border). All 12 result tests must pass. |

**Key ACs**:
- AC1–AC2: Confidence badge variants (emerald/amber/red) with CSS variables
- AC3: Low-confidence warning styling
- AC4–AC7: AnswerPanel, CitationList, CitationItem card styling with typography
- AC8–AC10: Loading spinner, empty state, no-source warning visible (existing states)
- AC11–AC12: All Tailwind removed, tests pass (12 tests green)

**Subagent dispatch**: Self-contained (CSS styling + className updates in 5 components, no logic changes).

---

### S005: Login page + HistoryPanel + HistoryItem styling

**Story**: As a user, I want login page branded with the indigo header aesthetic, history panel styled as a sidebar panel, and history items clearly clickable, so that login flow feels cohesive with app branding and I can easily scan past queries.

| Field | Value |
|-------|-------|
| **Agent** | frontend-agent |
| **Depends on** | S004 (component styling established) |
| **Parallelizable** | No (last in chain) |
| **Files modified** | `frontend/src/pages/LoginPage.tsx`, `frontend/src/components/auth/LoginForm.tsx`, `frontend/src/components/history/HistoryPanel.tsx`, `frontend/src/components/history/HistoryItem.tsx` |
| **ACs** | 8 |
| **Est. tokens** | 2.4k |
| **Test command** | `npm run test` (full suite, 208 tests) |
| **Definition** | Style LoginPage centered card layout: `<main>` flex center 100vh min-height, indigo gradient brand strip, card with surface background, border, shadow-lg, padding 32px, max-width 380px. LoginForm inputs: border, border-radius, `:focus` indigo ring, padding. Submit button: indigo gradient. HistoryPanel sidebar: surface background, border, border-radius, padding 16px. HistoryItem rows: clickable, cursor pointer, padding, hover state (--surface-2), truncated query text, DM Mono timestamp (HH:mm format, 11px, --text-3 color). |

**Key ACs**:
- AC1–AC3: LoginPage card layout, brand strip, input + button styling
- AC4–AC5: HistoryPanel sidebar, HistoryItem clickable rows with hover
- AC6–AC8: DM Mono timestamp, all Tailwind removed, full test suite passes (208 tests green)

**Subagent dispatch**: Self-contained (CSS styling + className updates in 4 components, no logic changes).

---

## Critical Path & Dependencies

```
S001: Create index.css + tokens
  ↓ (all S002–S005 depend on S001 tokens)
S002: Add sticky header + grid layout
  ↓ (S003–S005 depend on page layout)
S003: Style search area (input, button, selector)
  ↓ (S004–S005 depend on component styling approach)
S004: Style results (badges, panels, citations)
  ↓ (S005 depends on component CSS patterns)
S005: Style login + history panels
  ↓
DONE ✅ All stories complete
```

**No parallelization possible**: Each story builds on CSS tokens and layout decisions from previous stories. Sequential execution ensures consistency.

---

## Session Breakdown

### Session 1: S001–S005 (frontend-theme feature)
- Start: S001 (tokens + import, 30 min)
- Then: S002 (header + grid, 30 min)
- Then: S003 (search styling, 20 min)
- Then: S004 (results styling, 25 min)
- Then: S005 (login + history, 25 min)
- **Finalize**: `npm run test` (all 208 tests pass), `npm run build` (zero errors)
- **Deliverable**: Single commit with all 5 stories, all ACs green, ready for `/report`

---

## Quality Gates

**Per story**:
- All ACs checked (testable via `npm run test` or visual inspection)
- Zero TS errors in build
- No Tailwind classNames remaining
- All 208 tests still green

**End of feature**:
- /report frontend-theme (summary + all ACs traced)
- Commit message: `frontend-theme: design tokens + theme styling (S001–S005, 48 ACs)`
- Merge to main (no blocking issues)

---

## Next Steps

1. **Approve this plan**: Confirm critical path and session strategy
2. **Run `/tasks frontend-theme S001`**: First task definition for token creation
3. **Implement stories sequentially**: S001 → S002 → S003 → S004 → S005
4. **Finalize**: `/report frontend-theme` after all stories complete

---

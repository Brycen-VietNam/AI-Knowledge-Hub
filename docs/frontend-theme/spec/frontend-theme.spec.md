# Spec: frontend-theme
Created: 2026-04-17 | Author: Claude | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | Frontend SPA |
| Priority | P1 |
| Story count | 5 |
| Token budget est. | ~12k |
| Critical path | S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | None (sequential design system build) |
| Blocking specs | — |
| Blocked by | frontend-spa (S001–S005 DONE) |
| Agents needed | frontend-agent |

### Problem Statement
The React/Vite SPA is currently **unstyled** despite having a complete, polished design reference
in `docs/knowledge-hub.html`. Tailwind classNames exist in results components but Tailwind is not
installed, so no CSS is applied. Users see bare HTML with minimal layout. This blocks visual
launch and creates friction for stakeholders reviewing the platform.

### Solution Summary
- Extract design tokens (CSS variables) from knowledge-hub.html reference into `frontend/src/index.css`
- Import fonts (DM Sans, DM Mono, Playfair Display) via Google Fonts
- Apply theme progressively across 5 stories: baseline → header → search → results → login + panels
- Use plain CSS variables (no Tailwind, no new dependencies) for simplicity and maintainability
- Ensure all 208 existing tests still pass (styling is visual only)

### Out of Scope
- Dark mode / theme switching (single light theme only)
- Responsive design for mobile (desktop-first; responsive is post-launch)
- Storybook / component library documentation
- Figma / design tool sync
- Style animations beyond hover states
- Accessibility WCAG audit (trust existing semantic HTML)

---

## LAYER 2 — Story Detail (load per story for /tasks, /analyze, /implement)

### S001: Design tokens + global CSS baseline

**Role / Want / Value**
- As a: Frontend developer
- I want: A single CSS file with all design tokens (colors, shadows, radii, fonts) extracted from knowledge-hub.html
- So that: Components can reference `var(--indigo)` instead of hardcoded hex values, ensuring consistency and making theming maintainable

**Acceptance Criteria**
- [ ] AC1: `frontend/src/index.css` exists and is imported in `frontend/src/main.tsx` (before React root)
- [ ] AC2: CSS `:root` block defines ≥20 design tokens: `--bg`, `--surface`, `--surface-2`, `--border`, `--border-focus`, `--text`, `--text-2`, `--text-3`, `--indigo`, `--indigo-dark`, `--indigo-light`, `--sky`, `--sky-light`, `--emerald`, `--emerald-light`, `--amber`, `--amber-light`, `--red`, `--red-light`, `--shadow-sm`, `--shadow`, `--shadow-lg`, `--radius`, `--radius-sm`, `--header-h`
- [ ] AC3: All token values match knowledge-hub.html lines 11–37 exactly (colors, shadows, radii, header-h = 60px)
- [ ] AC4: `@import url(...)` for Google Fonts loads DM Sans (300/400/500/600), DM Mono (400/500), Playfair Display (700) synchronously
- [ ] AC5: `body { font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); }` is set
- [ ] AC6: Global `* { box-sizing: border-box; margin: 0; padding: 0; }` reset present
- [ ] AC7: `npm run build` passes with zero TS errors
- [ ] AC8: Visual check: page background is light blue-gray (--bg = #f0f2f7), text is near-black (--text = #1a1d2e), fonts render correctly

**Non-functional**
- No performance impact: CSS variables are native, no runtime overhead
- Font loading: async Google Fonts (non-critical path)

**Implementation notes**
Copy `:root`, `@import`, `body`, `*` CSS from knowledge-hub.html (lines 8–48).
Pay attention to font-family exact spelling: `DM Sans`, `DM Mono`, `Playfair Display`.

---

### S002: Header + app shell layout

**Role / Want / Value**
- As a: User / stakeholder
- I want: A sticky header with Brysen Group branding (logo, gradient background, user pill) and a grid-based app shell
- So that: The app looks professional, header stays visible while scrolling, and content area has proper spacing

**Acceptance Criteria**
- [ ] AC1: Header is `position: sticky; top: 0; z-index: 100; height: var(--header-h)` with indigo gradient background matching knowledge-hub.html (lines 51–59). Header renders on ALL pages (login + query).
- [ ] AC2: Header gradient is exactly `linear-gradient(135deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%)`
- [ ] AC3: Logo markup present in header: `.logo` flex container with `.logo-icon` (indigo gradient box with AI icon) and `.logo-text` (Playfair Display title `"Knowledge Hub"` + uppercase subtitle `"BRYSEN GROUP"`)
- [ ] AC4: User pill on header right: `.user-pill` with `.avatar` (circular, indigo gradient, initial letter) + `username` from `useAuthStore()`. **Hidden on LoginPage** (`token === null`). No role text.
- [ ] AC5: Language selector in header: `.lang-selector` pill with transparent white background, indigo-light text
- [ ] AC6: App body below header: `display: grid; grid-template-columns: 1fr 280px; gap: 20px; max-width: 1280px; margin: 0 auto; padding: 24px 24px 40px`
- [ ] AC7: Left column (main) is searchable area + results; right column is HistoryPanel (280px fixed width)
- [ ] AC8: All header styling matches knowledge-hub.html lines 50–119 visually
- [ ] AC9: HistoryPanel renders in right column (existing S004 component from frontend-spa)
- [ ] AC10: `npm run build` + `npm run test` both pass; all 208 tests still green

**Non-functional**
- Header sticky scroll behavior: smooth, no flicker
- Grid layout: max-width constraint prevents text line length > 120ch

**Implementation notes**
Add `<header>` to `App.tsx` (wraps all routes). Header always visible.
User pill: conditionally rendered — `token !== null` → show pill with `username`; `token === null` → hide.
Use CSS from knowledge-hub.html (lines 50–129) as reference.
Grid layout (`app-body`) placed in `QueryPage.tsx`, not `App.tsx` (login page has its own centered layout).

---

### S003: Search area + LanguageSelector styling

**Role / Want / Value**
- As a: User
- I want: A visually polished search card with proper input styling, character count badge, and inline language selector
- So that: Searching feels responsive and modern, not bare HTML

**Acceptance Criteria**
- [ ] AC1: SearchInput component wrapped in `.search-panel` card: `background: var(--surface)`, `border: 1px solid var(--border)`, `border-radius: var(--radius)`, `box-shadow: var(--shadow)`
- [ ] AC2: Search header bar (`.search-header`): `background: var(--surface-2)`, `padding: 14px 16px`, `border-bottom: 1px solid var(--border)`
- [ ] AC3: Textarea input has `border: 1px solid var(--border)`, `border-radius: var(--radius-sm)`, `:focus` ring uses `outline: 2px solid var(--border-focus)` (indigo)
- [ ] AC4: Submit button has indigo gradient: `background: linear-gradient(135deg, var(--indigo), var(--indigo-dark))`, white text, rounded, hover darkens
- [ ] AC5: Character count badge renders in DM Mono font, right-aligned in search header
- [ ] AC6: Inline language selector (LanguageSelector component) styled as pill: `background: rgba(99,102,241,.1)`, `border: 1px solid var(--border)`, `border-radius: 7px`, `padding: 5px 10px`, hover slightly brighter
- [ ] AC7: All colors/spacing match knowledge-hub.html lines 130–200 visually
- [ ] AC8: `npm run test -- tests/components/query/` passes; no regressions

**Non-functional**
- Input focus ring must be accessible (sufficient contrast)
- Button hover state must have visible feedback

**Implementation notes**
Apply CSS to `SearchInput.tsx` and `LanguageSelector.tsx`.
Reference knowledge-hub.html lines 130–200 for exact padding, shadows, border colors.

---

### S004: Results area styling (AnswerPanel, ConfidenceBadge, Citations)

**Role / Want / Value**
- As a: User
- I want: Results (answer, confidence, citations) displayed with proper color coding and card styling
- So that: I can quickly see answer confidence and source documents with visual hierarchy

**Acceptance Criteria**
- [ ] AC1: ConfidenceBadge variants use CSS variables (NOT non-functional Tailwind classNames):
  - HIGH (≥0.7): `background: var(--emerald-light)`, `color: var(--emerald)`, `border: 1px solid var(--emerald)`
  - MEDIUM (0.4–0.69): `background: var(--amber-light)`, `color: var(--amber)`, `border: 1px solid var(--amber)`
  - LOW (<0.4): `background: var(--red-light)`, `color: var(--red)`, `border: 1px solid var(--red)`
- [ ] AC2: Badge renders as inline-flex pill: `border-radius: var(--radius-sm)`, `padding: 4px 8px`, `font-size: 11px`, `font-weight: 600`
- [ ] AC3: LowConfidenceWarning (confidence < 0.4) renders as alert:
  - `background: var(--amber-light)`, `border: 1px solid var(--amber)`, `border-radius: var(--radius-sm)`,
  - `padding: 12px 16px`, `color: var(--amber)`
- [ ] AC4: AnswerPanel container: `background: var(--surface)`, `border: 1px solid var(--border)`, `border-radius: var(--radius)`, `box-shadow: var(--shadow)`, `padding: 20px`
- [ ] AC5: Markdown answer text rendered with prose typography: `font-family: 'DM Sans'`, `line-height: 1.6`, `font-size: 14px`, `color: var(--text)`
- [ ] AC6: CitationList renders as flex column, each CitationItem as card: `background: var(--surface-2)`, `padding: 12px`, `border-radius: var(--radius-sm)`, `border-bottom: 1px solid var(--border)`
- [ ] AC7: Citation score badge uses monospace (DM Mono): `font-family: 'DM Mono'`, small and right-aligned
- [ ] AC8: Loading spinner visible in AnswerPanel while isLoading=true
- [ ] AC9: Empty state message ("No results") visible when error=null, result=null
- [ ] AC10: "No source warning" message visible when result.answer but result.citations.length=0
- [ ] AC11: All Tailwind classNames removed from AnswerPanel, ConfidenceBadge, LowConfidenceWarning, CitationList, CitationItem (replace with CSS classes or inline styles using CSS variables)
- [ ] AC12: `npm run test -- tests/components/results/` passes; all 12 tests in AnswerPanel, ConfidenceBadge, LowConfidenceWarning, CitationList, CitationItem green

**Non-functional**
- Confidence colors must meet WCAG AAA contrast for text (ensure amber/red/green text is readable)
- Citation cards must be scannable (clear hierarchy, monospace scores)

**Implementation notes**
Remove/replace Tailwind classNames in:
- `frontend/src/components/results/AnswerPanel.tsx`
- `frontend/src/components/results/ConfidenceBadge.tsx`
- `frontend/src/components/results/LowConfidenceWarning.tsx`
- `frontend/src/components/results/CitationList.tsx`
- `frontend/src/components/results/CitationItem.tsx`

Approach: Add CSS classes to `frontend/src/index.css` (global). No CSS modules, no inline `style={{}}`.
Apply className strings (e.g. `className="confidence-badge high"`) referencing CSS vars in index.css.
Reference knowledge-hub.html confidence badge colors (lines 250–270).

---

### S005: Login page + HistoryPanel + HistoryItem styling

**Role / Want / Value**
- As a: User
- I want: Login page branded with the indigo header aesthetic, history panel styled as a sidebar panel, and history items clearly clickable
- So that: Login flow feels cohesive with the app branding, and I can easily scan and click past queries

**Acceptance Criteria**
- [ ] AC1: LoginPage centered card layout: `<main>` centered (flex, center, 100vh min-height), `<div class="login-card">` with:
  - Top: indigo gradient brand strip (same gradient as header, 4px tall or small section)
  - Card: `background: var(--surface)`, `border: 1px solid var(--border)`, `border-radius: var(--radius)`, `box-shadow: var(--shadow-lg)`, `padding: 32px`, `max-width: 380px`
  - Heading: `font-family: 'Playfair Display'`, `font-size: 24px`, `color: var(--text)`, margin bottom 20px
- [ ] AC2: LoginForm inputs styled: `border: 1px solid var(--border)`, `:focus` ring indigo, `padding: 10px 12px`, `border-radius: var(--radius-sm)`, `font-family: 'DM Sans'`
- [ ] AC3: Submit button: `background: linear-gradient(135deg, var(--indigo), var(--indigo-dark))`, white text, `padding: 10px 16px`, `border-radius: var(--radius-sm)`, hover state darkens
- [ ] AC4: HistoryPanel (existing S004 component from frontend-spa) now styled as sidebar:
  - `background: var(--surface)`, `border: 1px solid var(--border)`, `border-radius: var(--radius)`, `padding: 16px`
  - `<h2>` header: `color: var(--text)`, `font-size: 14px`, `font-weight: 600`, `margin-bottom: 12px`
  - Clear button: same gradient as submit buttons, `padding: 8px 12px`, small font
- [ ] AC5: HistoryItem (existing S004 component) each entry is clickable row:
  - `cursor: pointer`, `padding: 8px 12px`, `border-radius: var(--radius-sm)`, `:hover` background is `var(--surface-2)`
  - Query text: `color: var(--text)`, truncated at 60 chars
  - Timestamp: `font-family: 'DM Mono'`, `color: var(--text-3)`, `font-size: 11px`, HH:mm format
- [ ] AC6: No LoginForm or HistoryItem/HistoryPanel Tailwind classNames (all replaced with CSS)
- [ ] AC7: `npm run test -- tests/pages/LoginPage.test.tsx tests/components/history/` passes; all 9 tests green
- [ ] AC8: `npm run build` passes; `npm run test` (full suite, 208 tests) all green

**Non-functional**
- Login card max-width prevents unwanted wide layout
- History item click is keyboard-accessible (semantic HTML)
- Timestamp in DM Mono is readable at 11px

**Implementation notes**
Style LoginPage, LoginForm, HistoryPanel, HistoryItem components.
Add CSS classes to `frontend/src/index.css` (global). No CSS modules, no inline `style={{}}`.
All components reference CSS variables via className strings.
Reference knowledge-hub.html login section and history panel layout as visual guide.

---

## LAYER 3 — Sources Traceability (load for audit / design rationale)

### S001 Sources
| AC | Source | Reference | Date |
|---|---|---|---|
| AC2–AC3 | Design reference | docs/knowledge-hub.html lines 11–37 | 2026-04-16 |
| AC4 | Google Fonts API | https://fonts.google.com — DM Sans, DM Mono, Playfair Display | 2026-04-17 |
| AC5–AC6 | HTML reference | docs/knowledge-hub.html global reset | 2026-04-16 |

### S002 Sources
| AC | Source | Reference | Date |
|---|---|---|---|
| AC1–AC2, AC8 | Design reference | docs/knowledge-hub.html lines 50–119 (header + grid) | 2026-04-16 |
| AC6 | Grid layout spec | docs/knowledge-hub.html lines 121–128 | 2026-04-16 |
| AC9 | Frontend SPA S004 (frontend-spa.spec.md) | HistoryPanel component exists | 2026-04-16 |

### S003 Sources
| AC | Source | Reference | Date |
|---|---|---|---|
| AC1–AC6 | Design reference | docs/knowledge-hub.html lines 130–200 (search panel, lang selector) | 2026-04-16 |
| AC8 | Existing tests | tests/components/query/SearchInput.test.tsx | 2026-04-16 |

### S004 Sources
| AC | Source | Reference | Date |
|---|---|---|---|
| AC1–AC10 | Design reference | docs/knowledge-hub.html confidence badge colors, citation cards | 2026-04-16 |
| AC11 | Codebase audit | Existing Tailwind classNames in results components (Explore agent report) | 2026-04-17 |
| AC12 | Test suite | tests/components/results/ (12 tests, currently passing) | 2026-04-16 |

### S005 Sources
| AC | Source | Reference | Date |
|---|---|---|---|
| AC1 | Design reference | docs/knowledge-hub.html login card branding | 2026-04-16 |
| AC4–AC5 | Frontend SPA S004 | HistoryPanel + HistoryItem components | 2026-04-16 |
| AC7 | Test suite | tests/pages/LoginPage.test.tsx (6 tests), tests/components/history/ (10 tests) | 2026-04-16 |

---

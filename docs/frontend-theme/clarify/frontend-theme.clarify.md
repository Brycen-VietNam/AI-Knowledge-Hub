# Clarify: frontend-theme
Generated: 2026-04-17 | Spec: v1 DRAFT | Stories: S001–S005

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | Header on LoginPage? | Header renders on ALL pages. LoginPage: user pill hidden. QueryPage: user pill visible. ✅ Resolved 2026-04-17 | User | DONE |
| Q2 | Logo text strings? | "Knowledge Hub" (title) + "BRYSEN GROUP" (subtitle) — confirmed ✅ Resolved 2026-04-17 | User | DONE |
| Q3 | User pill data source + role? | `username` from `useAuthStore()` only. No role text shown. ✅ Resolved 2026-04-17 | User | DONE |
| Q4 | CSS approach for results components? | Global CSS classes in `index.css` (no modules, no inline style). ✅ Resolved 2026-04-17 | User | DONE |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q5 | S001 AC4: Spec says "synchronously" for Google Fonts `@import`. This blocks render. Should it be `@import` (sync/CSS) or `<link rel="preconnect" + stylesheet>` in index.html (non-blocking)? | **Default: `@import` in index.css** (simpler, matching knowledge-hub.html approach; performance concern is out of scope for MVP) |
| Q6 | S002 AC6: Grid layout `grid-template-columns: 1fr 280px` — HistoryPanel is hidden when history is empty (returns null). Should the grid collapse to `1fr` when HistoryPanel is absent, or stay as 2 columns with empty space? | **Default: always 2 columns** (HistoryPanel hidden ≠ grid change; keeps layout stable) |
| Q7 | S005 AC7: Spec says "9 tests green" for login + history. Current test count is: LoginPage (6 tests) + HistoryPanel (5 tests) + HistoryItem (5 tests) = 16, not 9. Should the AC be corrected to 16? | **Default: assume 16 tests** (6+5+5), update AC7 count |
| Q8 | S004 AC8–AC10: Loading spinner, empty state, no-source warning — the spec says "existing states; styling only". Confirm no new HTML needs to be added — these states already render correct text/elements in the current implementation. | **Default: yes, states already render** (confirmed by 208 passing tests) |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q9 | S002 AC5: LanguageSelector is already in the header from frontend-spa — should it be visually removed from the search area (S003 AC6) and only shown in the header? Or shown in both locations? |
| Q10 | S005 AC1: "4px tall brand strip" vs "small section" — should it be a thin `height: 4px` top bar or a taller section with logo text? |
| Q11 | Should `frontend/src/index.css` replace or sit alongside any existing `App.css` or `index.css` that Vite scaffolded? |

---

## Auto-answered from existing files

| # | Question | Answer | Source |
|---|----------|--------|--------|
| A1 | Should CSS use Tailwind? | No — D001 (CSS variables, no Tailwind) | WARM/frontend-theme.mem.md |
| A2 | Dark mode support? | No — D002 (single light theme, desktop-first MVP) | WARM/frontend-theme.mem.md |
| A3 | File name: tokens.css or index.css? | `index.css` — D003 (Vite convention, single global import) | WARM/frontend-theme.mem.md |
| A4 | Font families? | DM Sans (body), DM Mono (mono/score), Playfair Display (heading) — D004 | WARM/frontend-theme.mem.md |
| A5 | Do all 208 tests need to stay green? | Yes — styling is purely visual, no logic change expected | frontend-theme.spec.md S001 AC7, S005 AC8 |
| A6 | Mobile responsive? | Out of scope — desktop-first MVP | frontend-theme.spec.md Out of Scope |
| A7 | Are WCAG AA/AAA checks required? | No formal audit — trust existing semantic HTML | frontend-theme.spec.md Out of Scope |
| A8 | RBAC / auth rules apply to frontend? | No new routes; styling only — no HARD.md rules triggered | HARD.md scan |

---

## Summary

- **Blockers**: 4 (Q1–Q4 must be answered before /plan)
- **Auto-answered**: 8 (no ambiguity — resolved from memory and spec)
- **Should-resolve**: 4 (Q5–Q8 — defaults given, proceed if no answer by sprint start)
- **Nice-to-have**: 3 (Q9–Q11 — non-blocking, style preference only)

**Recommended action**: Answer Q1–Q4, then run `/checklist frontend-theme`.

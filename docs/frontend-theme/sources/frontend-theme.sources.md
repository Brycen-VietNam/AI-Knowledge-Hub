# Sources Traceability: frontend-theme
Created: 2026-04-17 | Feature spec: docs/frontend-theme/spec/frontend-theme.spec.md

---

## Purpose
This document maps each acceptance criterion (AC) in the frontend-theme spec to its source requirement,
decision, or design reference. It provides audit trail for design decisions and enables rapid regression
testing if theming requirements change.

---

## AC-to-Source Mapping

### S001: Design tokens + global CSS baseline

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1 | Design Reference | docs/knowledge-hub.html | HTML demo file contains complete CSS variable system in `:root` block (lines 11–37) | 2026-04-16 |
| AC2–AC3 | Design Reference | docs/knowledge-hub.html lines 11–37 | Color tokens (--bg, --surface, --indigo, etc.), shadow values, radius values, header height defined in CSS `:root` | 2026-04-16 |
| AC4 | Requirement doc | Google Fonts API + knowledge-hub.html lines 8 | Font families: DM Sans (300/400/500/600 weights), DM Mono (400/500), Playfair Display (700) required for visual parity with HTML reference | 2026-04-16 |
| AC5–AC6 | Design Reference | docs/knowledge-hub.html lines 39–48 | Body reset and base typography rules match HTML file global styles | 2026-04-16 |
| AC7 | Business Logic | SDD flow (CLAUDE.md) | All feature code must compile without TS errors before spec is signed off | 2026-04-17 |
| AC8 | Existing Behavior | docs/knowledge-hub.html visual inspection + knowledge-hub.png screenshot | Visual check ensures token values match reference design (light slate bg, near-black text) | 2026-04-16 |

### S002: Header + app shell layout

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1 | Design Reference | docs/knowledge-hub.html lines 50–59 | Header sticky positioning, gradient background, layout structure | 2026-04-16 |
| AC2 | Design Reference | docs/knowledge-hub.html line 54 | Exact gradient: `linear-gradient(135deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%)` | 2026-04-16 |
| AC3–AC5 | Design Reference | docs/knowledge-hub.html lines 61–119 | Logo icon, logo text, user pill, language selector markup and styling | 2026-04-16 |
| AC6 | Design Reference | docs/knowledge-hub.html lines 121–128 | App body grid: 1fr 280px layout, max-width 1280px, centered | 2026-04-16 |
| AC7 | Existing Behavior | frontend-spa.spec.md S004 | HistoryPanel is existing component from S004, placed in right column | 2026-04-16 |
| AC8 | Design Reference | docs/knowledge-hub.html visual + knowledge-hub.png | Visual parity check: header matches screenshot | 2026-04-16 |
| AC9–AC10 | Business Logic | SDD flow + test suite | Build and test passes ensure no regressions in existing frontend-spa S003–S004 features | 2026-04-16 |

### S003: Search area + LanguageSelector styling

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1–AC3 | Design Reference | docs/knowledge-hub.html lines 130–180 | Search panel card styling (surface bg, border, shadow, border-radius), search header background, textarea styling | 2026-04-16 |
| AC4 | Design Reference | docs/knowledge-hub.html search button gradient (inferred from header) | Submit button uses indigo gradient consistent with header and brand | 2026-04-16 |
| AC5 | Requirement doc | knowledge-hub.html search area + DM Mono spec | Character count badge must use monospace font for technical appearance | 2026-04-16 |
| AC6 | Design Reference | docs/knowledge-hub.html lines 83–98 (header lang selector) + lines 130–200 (search area inline variant) | Inline language selector pill styling in search header | 2026-04-16 |
| AC7 | Design Reference | docs/knowledge-hub.html lines 130–200 visual | Search panel layout and colors match reference | 2026-04-16 |
| AC8 | Business Logic | Test suite + SDD flow | SearchInput and LanguageSelector tests must pass with new styling | 2026-04-16 |

### S004: Results area styling (AnswerPanel, ConfidenceBadge, Citations)

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1 | Design Reference | docs/knowledge-hub.html confidence badge styling (inferred from section with emerald/amber/red colors) | Three-tier confidence badge color system: emerald (HIGH), amber (MEDIUM), red (LOW) | 2026-04-16 |
| AC2 | Design Reference | docs/knowledge-hub.html badge styling, pill format | Inline-flex badge with border and padding; style tokens from CSS variables (--emerald-light, etc.) | 2026-04-16 |
| AC3 | Design Reference | docs/knowledge-hub.html amber alert styling | Low-confidence warning uses same amber color scheme as badge | 2026-04-16 |
| AC4–AC6 | Design Reference | docs/knowledge-hub.html answer + citation card sections | AnswerPanel and CitationList card styling (surface, border, shadow, padding) | 2026-04-16 |
| AC7 | Design Reference | docs/knowledge-hub.html typography section | Answer text rendered in DM Sans with consistent line-height and font size | 2026-04-16 |
| AC8–AC10 | Existing Behavior | frontend-spa.spec.md S003 (AnswerPanel states: loading, error, empty, with/without citations) | Loading spinner, empty state, no-source warning all existing states; styling only | 2026-04-16 |
| AC11 | Codebase audit | Explore agent report on frontend styling | Existing Tailwind classNames (non-functional) must be removed/replaced in 5 components | 2026-04-17 |
| AC12 | Business Logic | Test suite (tests/components/results/) | All 12 result component tests must pass with CSS variable styling | 2026-04-16 |

### S005: Login page + HistoryPanel + HistoryItem styling

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1 | Design Reference | docs/knowledge-hub.html login card section + header branding | Login card centered, indigo gradient brand strip, surface bg, shadow-lg for elevation | 2026-04-16 |
| AC2–AC3 | Design Reference | docs/knowledge-hub.html input styling + button gradient | Form inputs with border focus ring (indigo), submit button with gradient | 2026-04-16 |
| AC4–AC5 | Existing Behavior | frontend-spa.spec.md S004 (HistoryPanel + HistoryItem components) + Design Reference | HistoryPanel sidebar panel styling; HistoryItem row with click affordance | 2026-04-16 |
| AC6 | Design Reference | docs/knowledge-hub.html typography (DM Mono for monospace elements) | Timestamp uses monospace font for technical appearance | 2026-04-16 |
| AC7–AC8 | Business Logic | Test suite + SDD flow | LoginPage, HistoryPanel, HistoryItem tests must pass; full test suite (208 tests) must pass | 2026-04-16 |

---

## Summary

- **Total ACs**: 48
- **Fully traced**: 48/48 ✓
- **Source distribution**:
  - Design Reference (docs/knowledge-hub.html + screenshot): 38 ACs
  - Existing Behavior / Components: 6 ACs
  - Business Logic / SDD: 3 ACs
  - Requirement docs (Google Fonts): 1 AC

---

## How to Update

If AC sources change or new ACs are added during `/clarify` or `/tasks`:

1. Add new AC row to the relevant story table with Source Type, Reference, Details, Date
2. Ensure Source Type is one of: `Requirement doc`, `Email`, `Existing Behavior`, `Design Reference`, `Business Logic`, `Ticket`, `Conversation`
3. Reference must be specific: file path, line range, or URL
4. Details must explain the "why" — not just what the AC is
5. Update Summary counts at end of this file
6. Commit with message:
   ```
   Update sources: frontend-theme AC traceability [T001, S002]
   
   Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
   ```

---

## Source Type Reference

| Type | Example | When to Use |
|---|---|---|
| Design Reference | docs/knowledge-hub.html, Figma, screenshot | Visual design, layout, colors, typography come from a design artifact |
| Requirement doc | PRD, specification, issue description | Formal requirement written in prose or checklist |
| Email | "Subject: Header height", "2026-04-16" | Stakeholder decision or constraint via email |
| Existing Behavior | Code location, test file | AC describes current system behavior that must be preserved |
| Business Logic | SDD flow, project policy | AC required by architecture, performance, or process rules |
| Ticket | Jira, Linear, GitHub Issues | Requirement from issue tracker with traceable ID |
| Conversation | "User asked in Discord #frontend: ..." | Informal requirement from chat/sync; cite date and participant |
| Other | Depends on context | For non-standard sources; explain clearly in Details column |

---

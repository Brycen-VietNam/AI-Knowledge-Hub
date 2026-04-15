# Citation Rendering Contract

Contract-Version: 1.0
Feature: answer-citation
Status: Active — do not change without bumping Contract-Version

---

## Purpose

This document defines how consumers (Web SPA, Teams bot, Slack bot) MUST render the `citations` array returned by `POST /v1/query`. Compliance with this contract ensures correct citation display and backward compatibility as the API evolves.

---

## Response Shape (reference)

```json
{
  "request_id": "...",
  "answer": "Contractors are entitled to [1] 10 days annual leave per contract year [2].",
  "sources": ["<uuid1>", "<uuid2>"],
  "citations": [
    { "doc_id": "<uuid1>", "title": "Leave Policy 2024", "source_url": "https://..." },
    { "doc_id": "<uuid2>", "title": "HR Handbook Q1", "source_url": null }
  ],
  "low_confidence": false,
  "reason": null
}
```

---

## Consumer Behaviors (AC1–AC9)

### AC1 — Contract Version Header

This document is versioned. The current version is **1.0**.

- Consumers MUST document which contract version they target.
- Breaking changes to the citation shape will increment the major version.
- Additive changes (new optional fields) will NOT increment the version.
- Check `CHANGELOG.md` in this directory for version history.

---

### AC2 — Inline Marker Mapping

The `answer` string may contain `[N]` markers (1-based integer).

```
"answer": "Contractors are entitled to [1] 10 days ..."
```

Mapping rule: `[N]` → `citations[N-1]` (0-indexed array).

| Marker | Resolves to |
|--------|-------------|
| `[1]` | `citations[0]` |
| `[2]` | `citations[1]` |
| `[N]` | `citations[N-1]` |

**Out-of-bounds (OOB) handling:** If `N > citations.length`, render `[N]` as plain text — do not throw, do not hide the sentence. Example: `[99]` with 3 citations → render as the literal string `[99]`.

---

### AC3 — Low Confidence Banner

When `low_confidence: true` appears in the response:

- Show a visible warning banner above or alongside the answer (e.g. "This answer may be incomplete or uncertain").
- Still render all citations normally — do not suppress them.
- `low_confidence` does not affect the `citations` array validity.

---

### AC4 — Null `source_url` Handling

Each `CitationObject` has a `source_url` field that may be `null`:

```json
{ "doc_id": "...", "title": "HR Handbook Q1", "source_url": null }
```

- `source_url` is not null: render as a clickable hyperlink (`<a href="...">Title</a>`).
- `source_url` is null: render title-only (plain text, no `<a>` tag, no `href`).
- Consumers MUST NEVER throw or error on `source_url: null`. Always check before rendering a link.

---

### AC5 — Citation Ordering Guarantee

`citations` is in the same order as `sources`.

```
sources[0]    ↔    citations[0]
sources[1]    ↔    citations[1]
```

Consumers may rely on this order. `citations[i].doc_id === sources[i]` is guaranteed.

---

### AC6 — Empty Citations

When `citations: []` (empty array):

- Hide the citation UI component entirely — do not render an empty list, empty section, or "No citations" message.
- The `answer` field may still be non-null. Render the answer normally.
- An empty `citations` array is a valid state (e.g. when `answer` is null, both are empty).

---

### AC7 — Backward Compatibility: `sources` Field

The `sources` field is preserved for backward compatibility.

- `sources` contains document UUIDs only (no titles, no URLs).
- `citations` is the richer successor — it contains `doc_id`, `title`, and `source_url`.
- Consumers MAY continue using `sources` for UUID lookups or audit links.
- Consumers SHOULD prefer `citations` for any display involving titles or URLs.
- Both fields are always present in the response (neither is omitted).

---

### AC8 — Lenient JSON Parsing Required

Consumers MUST use permissive/lenient JSON parsing:

- Extra fields in `CitationObject` that are not listed in this contract MUST be ignored, not rejected.
- Extra fields at the response root level MUST be ignored.
- Do not use strict schema validators that fail on unknown keys.
- Example: if a future version adds `CitationObject.page_number`, an AC8-compliant consumer continues to function correctly without a code change.

---

### AC9 — OOB Marker in Answer

The `answer` string may contain `[N]` markers where `N > citations.length`.

This is expected behavior (the LLM may generate markers beyond the number of retrieved documents in some edge cases).

**Consumer rule:** If `N > citations.length`, render `[N]` as plain text — do not error, do not hide the surrounding sentence. The rest of the answer continues to be rendered normally.

Example:
```
answer: "See policy [1], appendix [99] for details."
citations: [ { "doc_id": "...", "title": "Leave Policy", "source_url": null } ]
```

Correct rendering: `"See policy Leave Policy, appendix [99] for details."`

---

## Summary Table

| AC | Behavior | Fail mode to avoid |
|----|----------|--------------------|
| AC1 | Target contract version 1.0 | Silently ignoring contract changes |
| AC2 | `[N]` → `citations[N-1]`; OOB → plain text | Crash on OOB index |
| AC3 | `low_confidence: true` → show banner, keep citations | Suppressing citations |
| AC4 | `source_url: null` → title only (no href) | Null-href link or throw |
| AC5 | `citations` order = `sources` order | Re-sorting or de-duping |
| AC6 | `citations: []` → hide citation UI | Rendering empty list |
| AC7 | `sources` preserved; use `citations` for display | Dropping `sources` field |
| AC8 | Lenient JSON — ignore unknown fields | Strict parser rejecting new fields |
| AC9 | OOB `[N]` in answer → plain text | Error on missing `citations[N-1]` |

# Sources Traceability: {{FEATURE_NAME}}
Created: {{DATE}} | Feature spec: `docs/specs/{{FEATURE_NAME}}.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: {{Story Title}}

| AC | Source Type | Reference | Details | Date |
|-----|---|---|---|---|
| AC1: _[criteria]_ | Requirement doc | _[doc name, page]_ | _[short quote or description]_ | YYYY-MM-DD |
| AC2: _[criteria]_ | Email | _[sender, subject]_ | _[key points]_ | YYYY-MM-DD |
| AC3: _[criteria]_ | Existing behavior | _[system/code location]_ | _[current implementation]_ | YYYY-MM-DD |
| AC4: _[criteria]_ | Business logic | _[BrSE note / ticket]_ | _[rationale]_ | YYYY-MM-DD |
| AC5: _[criteria]_ | Conversation | _[attendees, meeting date]_ | _[decision point]_ | YYYY-MM-DD |

### Story S002: {{Story Title}}
| AC | Source Type | Reference | Details | Date |
|-----|---|---|---|---|
| AC1: | | | | |

---

## Summary

**Total ACs:** N
**Fully traced:** N/N ✓
**Pending sources:** 0

---

## How to Update

When spec changes or new ACs discovered:
1. Add row to relevant Story table
2. Include source type + reference (must be findable)
3. Add date
4. Update Summary section
5. Commit with message: `docs: update sources traceability for {{FEATURE_NAME}}`

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |

---

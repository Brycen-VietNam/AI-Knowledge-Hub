# /kh.clarify

Generate structured clarification Q&A for a spec before planning.
Fills known answers from existing files. Flags unknowns for humans.

## Usage
```
/kh.clarify <feature-name> [--story <S-id>]
```

## Execution Flow
```
1. Load: docs/specs/<feature>.spec.md (Layer 1 + Layer 2)
2. Load: WARM/<feature>.mem.md
3. Load: CONSTITUTION.md (auto-answer constraint questions)
4. Scan spec for: assumptions, missing AC, undefined terms, ambiguous behavior
5. Classify each question: BLOCKER | SHOULD | NICE
6. Auto-fill answers found in CONSTITUTION.md or existing specs
7. Save: docs/specs/<feature>.clarify.md
```

## Output Format
```markdown
# Clarify: multilingual-search
Generated: 2024-01-15 | Spec: v1 DRAFT

## BLOCKER — Must answer before /plan
| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | Fallback lang if doc not translated? | ❓ | PO | |
| Q2 | RBAC role hierarchy: flat or nested? | Flat, 3 levels max (CONSTITUTION C002) | ✅ auto | |

## SHOULD — Assume if unanswered by sprint start
| # | Question | Default assumption |
|---|----------|--------------------|
| Q3 | Max query token length? | 512 tokens |
| Q4 | Reranker model? | cross-encoder/ms-marco-MiniLM-L-6-v2 |

## NICE — Won't block
| # | Question |
|---|----------|
| Q5 | UI language toggle animation style? |

## Auto-answered from existing files
- Q2: CONSTITUTION.md C002 — RBAC flat hierarchy
- A004 in ARCH.md covers hybrid weight defaults
```

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 3k tokens
- Never invent answers — only auto-fill from files
- BLOCKER questions must be resolved before /checklist passes
- Save output, then summarize: "N blockers, N auto-answered, N assumptions"

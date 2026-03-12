# /kh.specify

Write a detailed 2-layer spec for a feature or user story.

## Usage
```
/kh.specify <feature-name> [--epic <epic>] [--priority P0|P1|P2]
```

## Examples
```
/kh.specify multilingual-search --epic rag-pipeline --priority P0
/kh.specify rbac-document-filter --epic auth
/kh.specify slack-bot-query-handler --epic bots
```

## Execution Flow
```
1. Load: CLAUDE.md + CONSTITUTION.md (check constraints)
2. Load: WARM/<feature>.mem.md if exists (resume, don't restart)
3. Copy template: .claude/templates/spec/_template.spec.md
4. Fill Layer 1 summary from inputs + constitution constraints
5. Generate Layer 2 stories (ask clarify questions inline if ambiguous)
6. Ask: source for each AC (requirement doc, email, existing behavior, business logic, conversation)
7. Save: docs/specs/<feature-name>.spec.md (Layers 1–3 including sources)
8. Save: docs/sources/<feature-name>.sources.md (sources traceability table)
9. Create: .claude/memory/WARM/<feature-name>.mem.md from template
10. Update: HOT.md — add to "In Progress" if P0
```

## Story count guidelines
| Scope      | Stories |
|------------|---------|
| Small task | 1–3     |
| Feature    | 3–7     |
| Epic       | 7–15    |

## Ambiguity handling
If a story requires assumptions → write them explicitly:
```markdown
> **Assumption**: Vietnamese BM25 uses underthesea tokenizer.
> Confirm or /clarify before /plan.
```
Do NOT silently assume. Do NOT block on minor details.

## Output
```
/kh.specify complete
  Spec:     docs/specs/multilingual-search.spec.md (Layers 1–3)
  Sources:  docs/sources/multilingual-search.sources.md
  Memory:   .claude/memory/WARM/multilingual-search.mem.md
  Stories:  5 | Assumptions: 2 | AC count: 12
  Next:     /clarify multilingual-search
```

## Agent Instructions
- Model: **sonnet** (claude-sonnet-4-6)
- Token budget: 3k tokens
- Load CONSTITUTION.md — flag violations before writing spec
- Three-layer structure is MANDATORY (Layer 1 summary + Layer 2 stories + Layer 3 sources)
- Output 3 files: spec.md + sources.md + WARM memory
- One spec file per feature, never merge features
- For each AC, ask stakeholder: "What is the source of this requirement?"
  - Accept: doc name, email date, ticket ID, code location, or "existing system"
  - Store in Layer 3 sources traceability table

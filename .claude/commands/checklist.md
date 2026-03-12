# /checklist

Pre-implementation gate. Validates spec quality, arch alignment, dependencies.
Must pass before /plan is allowed to proceed.

## Usage
```
/checklist <feature-name> [--story <S-id>]
```

## Execution Flow
```
1. Load: docs/specs/<feature>.spec.md (Layer 1 + Layer 2)
2. Load: docs/sources/<feature>.sources.md (check sources fully mapped)
3. Load: .claude/rules/HARD.md + ARCH.md (auto-check)
4. Load: CONSTITUTION.md (constraint check)
5. Auto-fill checklist template (AC coverage, scope impact, quality criteria)
6. Ask for human approval on any WARN items
7. Save: docs/reviews/<feature>.checklist.md
8. Output: PASS (proceed to /plan) | WARN (review approved) | FAIL (list blockers)
```

## Checklist

### Spec Quality
- [ ] Spec file exists at docs/specs/<feature>.spec.md
- [ ] Layer 1 summary complete (all fields filled)
- [ ] Layer 2 stories have clear AC statements (SMART criteria)
- [ ] Layer 3 sources fully mapped (each AC traced to source)
- [ ] All ACs are testable (not "should work well")
- [ ] API contract defined for every API story
- [ ] No silent assumptions (all marked explicitly)

### Architecture Alignment
- [ ] No CONSTITUTION violations
- [ ] No HARD rule violations in spec design
- [ ] Agent scope assignments match AGENTS.md registry
- [ ] Dependency direction follows ARCH.md A002
- [ ] pgvector/schema changes have migration plan
- [ ] Auth pattern specified (OIDC | API-key | both)

### Multilingual Completeness
- [ ] All 4 languages addressed: ja / en / vi / ko
- [ ] CJK tokenization strategy mentioned (if text processing)
- [ ] Response language behavior defined

### Dependencies
- [ ] Dependent specs: DONE or parallel-safe
- [ ] External contracts (embedding API, OIDC provider) locked
- [ ] No circular story dependencies

### Agent Readiness
- [ ] Token budget estimated in Layer 1
- [ ] Parallel-safe stories identified
- [ ] Subagent assignments listed

## Output
```markdown
## Checklist: multilingual-search
Result: ⛔ FAIL — 2 blockers

### ❌ Blockers (fix before /plan)
- Spec Quality: Q1 (fallback language) still ❓ in clarify.md
- Multilingual: Korean (ko) not mentioned in S003 RAG behavior

### ✅ Passed (14/16)
[list]

### Next
Resolve blockers → re-run /checklist → then /plan
```

## Agent Instructions
- Model: **haiku** (claude-haiku-4-5-20251001)
- Token budget: 3k tokens
- Hard stop if spec has ❌ CONSTITUTION violation
- Do NOT auto-fix spec — report and stop
- PASS = all items checked or explicitly marked N/A with reason

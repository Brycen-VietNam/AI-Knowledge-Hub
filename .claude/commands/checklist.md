# /checklist

Pre-implementation gate. Validates spec quality, arch alignment, dependencies.
Must pass before /plan is allowed to proceed.

## Usage
```
/checklist <feature-name> [--story <S-id>]
```

## Execution Flow
```
1. Load: docs/<feature>/spec/<feature>.spec.md (Layer 1 + Layer 2)
2. Load: docs/<feature>/sources/<feature>.sources.md (check sources fully mapped)
3. Load: docs/<feature>/clarify/<feature>.clarify.md (verify no unresolved BLOCKER questions)
4. Load: .claude/rules/HARD.md + ARCH.md + SECURITY.md + PERF.md (auto-check)
5. Load: AGENTS.md (verify agent scope assignments)
6. Load: CONSTITUTION.md (constraint check)
7. Auto-fill checklist template (AC coverage, scope impact, quality criteria)
8. For each WARN item: output formatted approval block (see WARN Approval Format)
9. Save: docs/<feature>/reviews/checklist.md
10. Output: PASS (proceed to /plan) | WARN (review approved) | FAIL (list blockers)
```

## WARN Approval Format
For each WARN item, output:
```markdown
⚠️ WARN: <item description>
Risk: <what could go wrong>
Mitigation: <how it will be handled>
Approve? [ ] Yes, proceed  [ ] No, resolve first
```
Human must check "Yes, proceed" before /checklist can output WARN-approved result.

## Checklist

### Spec Quality
- [ ] Spec file exists at docs/<feature>/spec/<feature>.spec.md
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
- [ ] Prompt caching strategy documented? (stable prefix + dynamic suffix + cache_control if API path)

### Prompt Caching Scoring Rule (Policy v1)
- If feature includes LLM prompts or subagent orchestration:
  - PASS: strategy documented with Route A (default) and Route B note (if direct Anthropic API path exists)
  - WARN (default): strategy missing/incomplete; require WARN approval block before continuing
  - FAIL: only when team explicitly enables strict gate for this feature
- If feature has no LLM path: mark item as N/A with short reason

## Output
```markdown
## Checklist: multilingual-search
Result: ⛔ FAIL — 2 blockers

### ❌ Blockers (fix before /plan)
- Spec Quality: Q1 (fallback language) still ❓ in clarify.md (unresolved BLOCKER)
- Multilingual: Korean (ko) not mentioned in S003 RAG behavior

### ✅ Passed (28/30)
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
- If clarify.md has any ❓ BLOCKER question → immediate FAIL, do not continue
- SECURITY.md + PERF.md loaded for Section 3 quality checks
- AGENTS.md loaded for "Agent scope assignments" item only

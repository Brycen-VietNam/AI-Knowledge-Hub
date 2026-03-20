# Knowledge-Hub — Claude Code Extension
# AI Spec-Driven Development (AI SDD) for Brysen Group

---

## Cách dùng

Mở project trong Claude Code → gõ `/` để thấy tất cả commands.

### SDD Flow
```
/constitution → /specify → /clarify → /checklist
     → /plan → /tasks → /analyze → /implement → /reviewcode
          ↓
     → /report
```

### Token-saving flow mỗi session
```bash
# 1. Bắt đầu session — load minimal context
/context <feature-name>

# 2. Kiểm tra rules trước khi làm
/rules --task T00X

# 3. Phân tích trước khi code
/analyze T00X

# 4. Implement (auto-hooks /rules pre)
/implement T00X

# 5. Review (auto-hooks /rules post)
/reviewcode T00X

# 6. Compress session sau ~10-15 turns
/sync --feature <feature-name>

# 7. Finalize after feature complete
/report <feature-name>
```

---

## Prompt Caching Strategy (Anthropic-first)

### Prompt Cache Policy v1 (document interface)
- `stable_prefix_rules`
- `dynamic_suffix_rules`
- `api_cache_control_policy` (optional, only for direct Anthropic API path)

### Route A (default): Stable Prefix
Use for all Claude Code slash-command and subagent handoff flows.
- Keep prefix fixed across calls: role/system, invariant rules, fixed file-load order, output contract.
- Put only volatile data in suffix: task id, fresh diff, blocker, user input.
- Reuse the same block order for higher cache hit and lower prompt cost.

### Route B (optional): Explicit `cache_control`
Use only when integrating direct Anthropic API calls outside normal slash-command flow.
- Apply `cache_control` to stable prompt blocks only.
- Keep Route A structure (stable prefix + dynamic suffix) even when `cache_control` is used.
- Not required for default Claude Code slash-command operation.

### Cache-breakers to avoid
- Changing stable block order between similar requests.
- Injecting timestamp/random/session-id into prefix.
- Inserting dynamic files/content at the beginning of prompt.

### Prompt frame (short template)
```text
Stable Prefix:
1) Role + invariant constraints
2) Fixed rule bundle order
3) Fixed file/context load order
4) Expected output contract

Dynamic Suffix:
- task_id / feature
- latest diff or runtime signal
- blocker / user-specific request

Expected Output:
- 3-line summary
- status + next action
```

---

## File Map

```
.claude/
├── CLAUDE.md               ← Project context + token budget rules (load EVERY session)
├── AGENTS.md               ← Subagent registry + compact handoff protocol
│
├── commands/               ← Slash commands (Claude Code auto-registers these)
│   ├── constitution.md     ← /constitution  — establish project principles
│   ├── specify.md          ← /specify       — write 2-layer feature spec
│   ├── clarify.md          ← /clarify       — Q&A before planning
│   ├── checklist.md        ← /checklist     — pre-plan gate
│   ├── plan.md             ← /plan          — 2-layer implementation plan
│   ├── tasks.md            ← /tasks         — atomic task breakdown
│   ├── analyze.md          ← /analyze       — codebase analysis before coding
│   ├── implement.md        ← /implement     — scoped implementation + hooks
│   ├── reviewcode.md       ← /reviewcode    — multi-level code review + hooks
│   ├── report.md           ← /report        — final summary + rollback plan
│   ├── sync.md             ← /sync          — compress session → memory files
│   ├── context.md          ← /context       — smart tiered context loader
│   └── rules.md            ← /rules         — rule checker (auto-hooked)
│
├── rules/                  ← Rule definitions (referenced by /rules command)
│   ├── HARD.md             ← R001–R007: security/data rules, never violate
│   ├── ARCH.md             ← A001–A006: architecture patterns
│   ├── SECURITY.md         ← S001–S005: injection, JWT, secrets
│   └── PERF.md             ← P001–P005: latency, batching, indexes
│
├── memory/                 ← Persistent memory (git-tracked)
│   ├── HOT.md              ← Sprint context — loaded EVERY session
│   ├── WARM/
│   │   └── _template.mem.md   ← Copy per feature at /specify
│   └── COLD/
│       └── README.md          ← Archive index for completed features
│
└── templates/              ← Source of truth for output formats
    ├── constitution/
    │   └── _template.constitution.md
    ├── spec/
    │   └── _template.spec.md (Layers 1–3 with sources traceability)
    ├── sources/
    │   └── _template.sources.md (AC-to-requirement mapping)
    ├── checklist/
    │   └── _template.checklist.md (pre-plan validation gate)
    ├── plan/
    │   └── _template.plan.md
    ├── tasks/
    │   └── _template.tasks.md
    └── report/
        └── _template.report.md (final summary + rollback)
```

---

## Memory Strategy

| Layer | File | Load when | Updated by |
|-------|------|-----------|------------|
| HOT | memory/HOT.md | Every session | /sync |
| WARM | memory/WARM/<feature>.mem.md | Working on that feature | /sync, /specify |
| COLD | memory/COLD/<feature>.archive.md | Explicitly requested | Manual archive |
| Project | CLAUDE.md | Every session | Manual (rare) |

---

## Rule Hooks

| Command | Pre-hook | Post-hook |
|---------|----------|-----------|
| /implement | /rules --phase pre (blocks on ❌) | /sync if > 10 turns |
| /reviewcode | — | /rules --phase post (blocks APPROVED on ❌) |
| /checklist | reads HARD.md + ARCH.md + CONSTITUTION | — |
| /plan | reads ARCH.md agent scope | — |

---

## Onboarding mới cho member

```bash
# Bước 1: Clone project
git clone <repo> && cd knowledge-hub

# Bước 2: Mở Claude Code
claude .

# Bước 3: Đọc context
/context                    # loads HOT.md — xem sprint hiện tại

# Bước 4: Nhận task từ team lead, implement
/context multilingual-search --task T003
/analyze T003
/implement T003
/reviewcode T003
```

Không cần config thêm gì. Tất cả đã có trong `.claude/`.

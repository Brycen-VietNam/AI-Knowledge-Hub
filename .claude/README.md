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

## Prompt Caching

See: `.claude/PROMPT_CACHING.md`

---

## File Map

```
.claude/
├── CLAUDE.md               ← Project context + token budget rules (load EVERY session)
├── AGENTS.md               ← Subagent registry + compact handoff protocol
├── PROMPT_CACHING.md       ← Prompt caching policy and management guidelines
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
| COLD | memory/COLD/<feature>.archive.md ¹ | Explicitly requested | Manual archive via /report |
| Project | CLAUDE.md | Every session | Manual (rare) |

¹ COLD stays flat (not nested under feature dir). Archive index in `COLD/README.md` references completed features.

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

---

## 📁 Feature Documentation Structure (as of 2026-03-24)

All feature artifacts are grouped under a single feature directory for scalability and clarity.

### Pattern
```
docs/<feature-name>/
  ├── spec/              # Specification (Layers 1–3)
  │   └── <feature>.spec.md
  ├── sources/           # AC traceability table
  │   └── <feature>.sources.md
  ├── clarify/           # Q&A resolution log
  │   └── <feature>.clarify.md
  ├── plan/              # Implementation plan
  │   └── <feature>.plan.md
  ├── tasks/             # Task definitions & analysis
  │   ├── <story>.tasks.md
  │   └── <story>.analysis.md
  ├── reviews/           # Code reviews & checklists
  │   ├── checklist.md
  │   └── <story>[-<task>].review.md
  └── reports/           # Final reports & rollback plans
      ├── <feature>.report.md
      └── <story>.report.md (per-story, if applicable)
```

### Example: auth-api-key-oidc
```
docs/auth-api-key-oidc/
├── spec/auth-api-key-oidc.spec.md
├── sources/auth-api-key-oidc.sources.md
├── clarify/auth-api-key-oidc.clarify.md
├── plan/auth-api-key-oidc.plan.md
├── tasks/
│   ├── S001.tasks.md
│   ├── S001.analysis.md
│   ├── S002.tasks.md
│   └── ...
├── reviews/
│   ├── checklist.md
│   ├── S001-T001.review.md
│   ├── S001-T002.review.md
│   └── ...
└── reports/
    ├── auth-api-key-oidc.report.md
    └── (no per-story reports in this case)
```

### Why this structure? (as of 2026-03-24)
- **Feature-centric:** All docs for one feature in one place
- **Scalable:** Handles 10+ concurrent features without flat directory bloat (previously specs/, plans/, reviews/ had 100+ files each)
- **Archive-friendly:** One feature directory = one atomic unit to move to `.claude/memory/COLD/` when done
- **Navigation:** Jump to `docs/rbac-document-filter/` and see all artifacts for that feature
- **Command integration:** All 10 slash commands (`/specify` through `/report`) updated to use this structure (refactor completed 2026-03-24)

### Transition note
Previously: `docs/specs/<feature>.spec.md`, `docs/plans/<feature>.plan.md`, `docs/tasks/<feature>/<story>.tasks.md`
Now: `docs/<feature>/spec/<feature>.spec.md`, `docs/<feature>/plan/<feature>.plan.md`, `docs/<feature>/tasks/<story>.tasks.md`

Existing features (db-schema-embeddings, auth-api-key-oidc) have been migrated. All new features follow this pattern automatically.

# Clarify: db-schema-embeddings
Generated: 2026-03-18 | Spec: v1 DRAFT | Status: COMPLETE

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Resolved |
|---|----------|--------|-------|----------|
| Q1 | asyncpg driver xác nhận? (`postgresql+asyncpg://`) | **asyncpg confirmed** — Apache 2.0, pure Python, fastest async driver | Stakeholder | ✅ 2026-03-18 |
| Q2 | Pool split: `pool_size=5 + max_overflow=15` vs `pool_size=10 + max_overflow=10`? | **pool_size=5, max_overflow=15** — 5 persistent + 15 burst = max 20 (C011) | Stakeholder | ✅ 2026-03-18 |
| Q3 | CJK tokenization: app layer hay PostgreSQL trigger? | **App layer** — PostgreSQL built-in parser không hỗ trợ CJK. rag-agent ghi `content_fts` sau khi tokenize. | Auto (D02) | ✅ 2026-03-17 |

---

## SHOULD — Confirmed / auto-answered

| # | Question | Answer | Source |
|---|----------|--------|--------|
| Q4 | Embedding vector dimension? | **1024** dims — multilingual-e5-large | Stakeholder, 2026-03-17 |
| Q5 | Vector similarity metric? | **Cosine** (`vector_cosine_ops`) | PERF.md P003 |
| Q6 | HNSW params (m, ef_construction)? | **m=16, ef_construction=64** | PERF.md P003 |
| Q7 | PK type cho tất cả bảng? | **UUID v4** (`gen_random_uuid()`) | CONSTITUTION C002, spec S001 |
| Q8 | `user_group_id` type: UUID hay INT? | **INT** — keeps FK joins simple | Spec S001 impl notes |
| Q9 | lang column format? | **CHAR(2)** ISO 639-1: ja/en/vi/ko/zh | Spec S001 |
| Q10 | Migration file naming convention? | **NNN_description.sql** với rollback section | CONSTITUTION C010, ARCH A006 |
| Q11 | Korean tokenizer? | **kiwipiepy** (MIT, no Java) thay KoNLPy | CONSTITUTION C005 v1.3 |
| Q12 | ORM model update timing? | **Sau** migration file được tạo và review | CONSTITUTION C010 |

---

## NICE — Won't block

| # | Question | Note |
|---|----------|------|
| Q13 | pgvector version tối thiểu? | 0.5.0+ (HNSW support). Confirm tại infra setup, không block schema. |
| Q14 | PostgreSQL version tối thiểu? | 14+ (gen_random_uuid native). Confirm tại infra setup. |
| Q15 | `audit_logs.user_id` là UUID hay string? | Phụ thuộc auth schema — db-agent để `TEXT` làm placeholder cho đến khi auth spec xong. |

---

## Auto-answered from existing files

| Question | Source | Reference |
|----------|--------|-----------|
| RBAC filter ở DB layer, không post-retrieval | CONSTITUTION.md | C001 |
| PII không được lưu trong vector metadata | CONSTITUTION.md | C002 |
| Audit log bắt buộc mỗi lần retrieval | CONSTITUTION.md | C008 |
| Connection pool min=5, max=20 | CONSTITUTION.md | C011 |
| HNSW index bắt buộc, no sequential scan | PERF.md | P003 |
| CJK tokenizer: MeCab/kiwipiepy/jieba/underthesea | CONSTITUTION.md | C005, C006 |
| Không được per-request connection | PERF.md | P005 |

---

## Spec corrections needed

| # | Story | Issue | Fix |
|---|-------|-------|-----|
| F1 | S003 | Implementation note còn ghi "KoNLPy" (cũ) | Update → **kiwipiepy** (đã đổi ở CONSTITUTION v1.3) |
| F2 | S004 | AC1 ghi `pool_size=10, max_overflow=10` | Update → **pool_size=5, max_overflow=15** (confirmed Q2) |

---

## Summary
**3 BLOCKERs** — tất cả resolved ✅
**10 SHOULD** — tất cả auto-answered ✅
**3 NICE** — không block planning
**2 spec corrections** cần update trước /checklist

**Next:** Update spec S003 + S004 → chạy `/checklist db-schema-embeddings`

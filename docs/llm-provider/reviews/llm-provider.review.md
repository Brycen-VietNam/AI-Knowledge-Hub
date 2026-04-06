## Code Review: llm-provider (post-fix re-review)
Level: security | Date: 2026-04-06 | Reviewer: Claude Opus

### Previous Issues — Resolution Check
- [x] B001: openai.py AsyncOpenAI + await — confirmed (openai.py:34 `openai.AsyncOpenAI`, openai.py:35 `await client.chat.completions.create`)
- [x] B001: claude.py AsyncAnthropic + await — confirmed (claude.py:35 `anthropic.AsyncAnthropic`, claude.py:36 `await client.messages.create`)
- [x] W001: LLM_TIMEOUT_S env var in ollama.py — confirmed (ollama.py:23 `float(os.getenv("LLM_TIMEOUT_S", "5.0"))`, used at ollama.py:39)
- [x] W002: Docstrings on base.py + adapters — confirmed (base.py:7 LLMResponse, base.py:18 LLMProvider, base.py:25 complete(); ollama.py:12 OllamaAdapter; openai.py:10 OpenAIAdapter; claude.py:10 ClaudeAdapter)
- [x] W003: asyncio.wait_for around generate_answer() — confirmed (query.py:136-138 `asyncio.wait_for(generate_answer(...), timeout=1.8)` with LLM_TIMEOUT 504 response at query.py:140-148)
- [x] W004: factory.reset() classmethod present — confirmed (factory.py:26-29 `cls._instances.clear()` under lock)

### Full Checks

| Check | Status | Reference |
|-------|--------|-----------|
| No files modified outside TOUCH list | PASS | Changes confined to backend/rag/llm/, backend/rag/generator.py, backend/api/routes/query.py, requirements.txt |
| Error handling: all external calls have try/except | PASS | ollama.py:43-44, openai.py:39-40, claude.py:41-42 — all wrap to LLMError |
| No magic numbers inline | PASS | Timeouts via env var (ollama.py:23); confidence sentinel 0.9 annotated with D06 decision; threshold 0.4 from spec; max_tokens=1024 is SDK convention |
| Docstrings on new public functions/classes | PASS | All public classes, abstract methods, and service functions documented |
| No commented-out dead code | PASS | Inline comments are spec/task/decision references only |

### Security Checks

| Rule | Status | File:Line | Notes |
|------|--------|-----------|-------|
| R001 — RBAC WHERE clause intact | PASS | query.py:116 | `user_group_ids=user.user_group_ids` passed to `retrieve()` |
| R003 — verify_token on /v1/query | PASS | query.py:98 | `Depends(verify_token)` present |
| R006 — audit_log background task | PASS | query.py:132 | `background_tasks.add_task(_write_audit, ...)` called before LLM generation |
| S001 — Zero SQL string interpolation | PASS | All DB writes via ORM `session.add()` (query.py:80); no raw SQL in any reviewed file |
| S003 — Input length limit | PASS | query.py:40 | `max_length=512` on `QueryRequest.query` |
| S005 — No hardcoded secrets or base URLs | PASS | All via `os.getenv()`: ollama.py:21-23, openai.py:20-21, claude.py:20-21, factory.py:17 |
| R007 — asyncio.wait_for on retrieval | PASS | query.py:113 | `asyncio.wait_for(retrieve(...), timeout=1.8)` |
| R007 — asyncio.wait_for on LLM generation | PASS | query.py:136 | `asyncio.wait_for(generate_answer(...), timeout=1.8)` |
| R007 — Timeout error responses follow A005 shape | PASS | query.py:122-130 QUERY_TIMEOUT 504; query.py:140-148 LLM_TIMEOUT 504 — both include code, message, request_id |

### Issues Found

#### BLOCKER — Must fix before merge
None.

#### WARNING — Should fix
None. All previous warnings (W001-W004) and blocker (B001) are resolved.

---
### Verdict
[x] APPROVED  [ ] CHANGES REQUIRED  [ ] BLOCKED

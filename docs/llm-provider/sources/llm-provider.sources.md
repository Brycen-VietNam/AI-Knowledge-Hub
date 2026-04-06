# Sources Traceability: llm-provider
Generated: 2026-04-06 | Spec: docs/llm-provider/spec/llm-provider.spec.md

---

## Master AC → Source Table

| Story | AC | Description | Source Type | Reference | Date |
|-------|-----|-------------|-------------|-----------|------|
| S001 | AC1 | LLMProvider ABC | Constitution | C015 — LLM_PROVIDER env var | 2026-03-18 |
| S001 | AC2 | LLMResponse dataclass | Business logic | Conversation lb_mui 2026-04-06 | 2026-04-06 |
| S001 | AC3 | LLMError exception | Constitution | P005 — fail fast, fail visibly | 2026-03-18 |
| S001 | AC4 | NoRelevantChunksError | Constitution | C014 — no answer without source | 2026-03-18 |
| S001 | AC5 | LowConfidenceWarning flag | Constitution | C014 — confidence < 0.4 | 2026-03-18 |
| S002 | AC1 | OllamaAdapter default | Constitution | C015 — "Default: ollama" | 2026-03-18 |
| S002 | AC2 | OpenAIAdapter | Constitution | C015 — supported providers list | 2026-03-18 |
| S002 | AC3 | ClaudeAdapter | Constitution | C015 — supported providers list | 2026-03-18 |
| S002 | AC4 | LLMError wraps SDK exceptions | Constitution | P005 — fail fast | 2026-03-18 |
| S002 | AC5 | No hardcoded secrets | Security rule | SECURITY.md S005 | 2026-03-18 |
| S002 | AC6 | Prompt template file | Business logic | Conversation lb_mui 2026-04-06 | 2026-04-06 |
| S002 | AC7 | Confidence + low_confidence flag | Constitution | C014 — confidence < 0.4 | 2026-03-18 |
| S003 | AC1 | LLM_PROVIDER env var dispatch | Constitution | C015 | 2026-03-18 |
| S003 | AC2 | Default "ollama" when unset | Constitution | C015 | 2026-03-18 |
| S003 | AC3 | Unknown provider → LLMError | Constitution | P005 — fail fast | 2026-03-18 |
| S003 | AC4 | Singleton per provider | Business logic | Pattern from cjk-tokenizer D05 | 2026-04-06 |
| S003 | AC5 | Clean public __init__.py API | Business logic | Conversation lb_mui 2026-04-06 | 2026-04-06 |
| S004 | AC1–AC4 | Mock-based unit tests (all 3 adapters) | Constitution | Testing policy ≥80% coverage | 2026-03-18 |
| S004 | AC5 | NoRelevantChunks regression | Constitution | C014 — critical no-hallucination guard | 2026-03-18 |
| S004 | AC6 | LowConfidence regression | Constitution | C014 | 2026-03-18 |
| S004 | AC7 | Factory tests all providers | Business logic | Pattern from TestTokenizerFactory | 2026-04-06 |
| S004 | AC8 | ≥80% coverage threshold | Constitution | Testing policy | 2026-03-18 |

---

## Constitution Constraints Satisfied

| Constraint | How |
|-----------|-----|
| C014 — cite source / no hallucination | `NoRelevantChunksError` gates generation; `low_confidence` flag at < 0.4 |
| C015 — LLM_PROVIDER configurable | `LLMProviderFactory.get()` reads env var; default = ollama |
| S005 — no hardcoded secrets | All keys via `os.getenv()` |
| P005 — fail fast | `LLMError` wraps all provider failures; unknown provider raises immediately |
| P008 — agent boundary | `backend/rag/llm/` owned by rag-agent; api-agent accesses only via factory |

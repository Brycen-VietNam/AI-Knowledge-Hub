---
name: Temp — LLM bypassed in query route
description: query route tạm thời bỏ qua LLM generation, trả sources trực tiếp từ retrieval
type: project
---

`backend/api/routes/query.py` — LLM generation block đã bị thay bằng return sources trực tiếp.

**Why:** Ollama chưa có LLM model (chỉ có mxbai-embed-large). Cần test retrieval pipeline trước khi pull LLM model.

**How to apply:** Khi LLM model đã sẵn sàng, revert đoạn này về logic gốc (generate_answer + llm_result). Tìm comment `# llm_disabled` trong file để locate.

**Revert khi:** `docker exec knowledge-hub-ollama ollama pull qwen2.5:0.5b` + set `LLM_MODEL=qwen2.5:0.5b` trong `.env`.

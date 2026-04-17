# Clarify: frontend-spa
Generated: 2026-04-16 | Updated: 2026-04-16 | Spec: v1 DRAFT | Stories: S000–S005 | ACs: 45

---

## BLOCKER — Must answer before /plan

| # | Story | Question | Answer | Owner | Due |
|---|-------|----------|--------|-------|-----|
| Q1 | S000 | `users` table có sẵn chưa (từ auth feature)? Migration NNN_add_password_hash.sql cần biết số migration tiếp theo (NNN). | ✅ Table tồn tại (migration 004). Thiếu `password_hash` column. Migration tiếp theo = **008**. | lb_mui | ✅ |
| Q2 | S000 | `AUTH_SECRET_KEY` đã có trong `.env` / secret store chưa? | ✅ Chưa có → cần generate + add vào `.env` & `.env.example` (S000 task scope) | lb_mui | ✅ |
| Q3 | S001 | Token refresh strategy: SPA tự refresh gần hết hạn hay chỉ redirect khi 401? | ✅ Tự refresh khi gần hết hạn (proactive refresh) | lb_mui | ✅ |
| Q4 | S002 | Citation score format: hiển thị "91%" hay "0.91"? | ✅ **"91%"** | lb_mui | ✅ |
| Q5 | S005 | Port mapping Docker: external port nên dùng bao nhiêu? | ✅ **`8080:80`** | lb_mui | ✅ |

---

## SHOULD — Assume nếu chưa trả lời trước sprint start

| # | Story | Question | Default assumption |
|---|-------|----------|--------------------|
| Q6 | S000 | Rate limit backend cho `/v1/auth/token`: dùng Valkey (C016) hay in-memory (SlowAPI)? | Valkey (SlowAPI + Valkey, nhất quán với C016) |
| Q7 | S001 | Trường hợp backend down khi user đang login: SPA hiển thị "Service unavailable" hay generic "Login failed"? | "Service unavailable" — dùng axios error status detection |
| Q8 | S002 | IME composition event (Japanese/Korean): có cần prevent-submit khi đang compose (compositionstart → compositionend) không? | Yes — block Enter submit khi `isComposing=true` |
| Q9 | S003 | Không có citations (empty array) nhưng có answer: hiển thị answer hay hiện "No relevant documents found"? | Spec AC6 nói "Không có kết quả" → hiện no-results message. Nếu có answer + empty citations → hiện warning thay vì block. |
| Q10 | S004 | History sidebar: luôn hiển thị hay chỉ show khi có ≥1 item? | Ẩn khi empty, hiện khi ≥1 item |
| Q11 | S005 | `.env.example` cần những env vars nào ngoài `VITE_API_BASE_URL`? | `VITE_API_BASE_URL` là var duy nhất cần thiết cho frontend |

---

## NICE — Không block

| # | Story | Question |
|---|-------|----------|
| Q12 | S002 | Language auto-detect từ `navigator.language`: map `ja-JP` → `ja`, `ko-KR` → `ko`, `vi-VN` → `vi`? Hay chỉ check prefix? |
| Q13 | S003 | Markdown rendering: có cần sanitize HTML trong answer (DOMPurify) hay react-markdown đủ safe? |
| Q14 | S003 | Confidence badge: có tooltip giải thích HIGH/MEDIUM/LOW thresholds không? |
| Q15 | S004 | History list: có nút "Clear history" không, hay chỉ clear tự động khi logout? |
| Q16 | S001 | Login page: có logo Brysen Group không, hay plain form? |

---

---

## Notes — Q2, Q4, Q5 Explained

### Q2 — AUTH_SECRET_KEY là gì và tại sao cần xác nhận?

`AUTH_SECRET_KEY` là secret dùng để **ký JWT** bằng thuật toán HS256 (symmetric key).
- Ai có key này có thể **tạo JWT giả** và bypass authentication → đây là secret quan trọng bậc nhất.
- Yêu cầu: **≥ 32 bytes random** (256-bit entropy), ví dụ: `openssl rand -hex 32`

**Tại sao cần hỏi:**
- Nếu key chưa tồn tại → cần generate và add vào `.env`, `.env.example` (placeholder), và CI/CD secrets store.
- Nếu key đã có trong `.env` → chỉ cần đảm bảo nó đủ mạnh (≥ 32 bytes) và không bị commit vào git.
- `AUTH_SECRET_KEY` **khác với** `OPENAI_API_KEY` hay `POSTGRES_PASSWORD` đang có — đây là key mới cho S000.

**Cần biết:** Key này đã có trong `.env` chưa (check xem có dòng `AUTH_SECRET_KEY=...` không)?

---

### Q4 — Citation score format

Hai lựa chọn:
- **"91%"** → thân thiện với end-user, dễ đọc hơn
- **"0.91"** → nhất quán với backend response (field `score: 0.91` trong `/v1/query`)

Gợi ý: **"91%"** cho citation display (UX), nhưng giữ raw value trong tooltip nếu cần debug. Bạn muốn theo hướng nào?

---

### Q5 — Docker port recommendation: `8080:80`

docker-compose.yml hiện tại đang dùng:
- `app` (backend FastAPI): `8000:8000`
- `postgres`: `5432:5432`
- `valkey`: `6379:6379`
- `ollama`: `11434:11434`

**Đề xuất `8080:80`** cho frontend-spa vì:
1. Port 80 thường bị block trên dev machine (cần root/admin)
2. Port 3000 thường dùng cho dev server (`npm run dev`) — giữ riêng để không nhầm
3. `8080` là convention phổ biến cho HTTP proxy/static server, không conflict
4. Production: reverse proxy (nginx/Traefik) sẽ map `443 → 8080` hoặc dùng host networking

Vậy docker-compose thêm:
```yaml
frontend-spa:
  ports:
    - "8080:80"
```

---

## Auto-answered from existing files

| # | Source | Answer |
|---|--------|--------|
| Q-A1 | CONSTITUTION.md C013 | Rate limit `/v1/query`: 60 req/min per user — SPA phải handle 429 gracefully |
| Q-A2 | CONSTITUTION.md C014 | Confidence < 0.4 triggers low-confidence warning → S003 AC4 confirmed |
| Q-A3 | CONSTITUTION.md C003 | `/v1/health` sole exception to auth → `/v1/auth/token` needs explicit spec exception (S000 AC7 confirmed) |
| Q-A4 | HARD.md R003 | `verify_token` dependency pattern — S000 AC9 dual-mode confirmed by existing oidc.py |
| Q-A5 | WARM D002 | JWT in-memory (không localStorage) — OWASP XSS prevention decided |
| Q-A6 | WARM D003 | UI language persist localStorage — session token NOT localStorage; language pref OK |
| Q-A7 | WARM D004 | Query history: session-only, in-memory — no API call needed |
| Q-A8 | ARCH.md A004 | BM25/Dense weights env-configurable — không liên quan frontend (confirmed out-of-scope) |
| Q-A9 | WARM A001 | `/v1/query` response shape stable (answer-citation + confidence-scoring DONE) → S003 API contract locked |
| Q-A10 | CONSTITUTION.md C016 | Rate limit backend = Valkey (Q6 default = Valkey confirmed by constraint) |

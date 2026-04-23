---
name: DEFERRED-SEC-001 — remove raw password from authStore
description: Password plaintext in Zustand memory is tech debt; fix via refresh-token endpoint in a future security sprint
type: feedback
---

Raw password should NOT be stored in `authStore` long-term. Implement `POST /v1/auth/refresh` refresh-token endpoint so force-change gate (`ChangePasswordPage`) no longer needs `authStore.password` as the silent `current_password`.

**Why:** Password plaintext lives in JS heap for the full session (~60 min). XSS risk. Logged as DEFERRED-SEC-001 in change-password report.

**How to apply:** When starting a security hardening sprint or implementing refresh-token support, pick this up. File to change: `frontend/src/store/authStore.ts` (remove `password` field), `frontend/src/pages/ChangePasswordPage.tsx` (remove silent pass), `backend/api/routes/auth.py` (add `/v1/auth/refresh`).

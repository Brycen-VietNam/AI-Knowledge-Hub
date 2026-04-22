---
name: Dev API key for local testing
description: Local dev API key for manual testing against Docker environment
type: project
---

**Dev API key:** `test-api-key-dev`

User: `dev@example.com` (sub: `dev-local`), `user_group_ids = [1]`

**Why:** Created manually via psql to unblock manual API testing in Docker. No `user_groups` row for id=1 yet — use `"user_group_id": null` for public docs to avoid FK error.

**How to apply:** Always pass `X-API-Key: test-api-key-dev` when testing endpoints locally. If DB volume is wiped (`down -v`), need to re-insert user + api_key.

apikey: kh_4eea3eb9fbd7b5d313a50f3c0d75e2ab

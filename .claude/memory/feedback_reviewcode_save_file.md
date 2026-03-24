---
name: reviewcode_save_file
description: /reviewcode must always save review file to docs/reviews/ — do not wait for user to ask
type: feedback
---

After every /reviewcode run, ALWAYS save the review output to `docs/reviews/<feature>.<task-id>.review.md` as part of the command's execution flow (step 7 in the command spec).

**Why:** The reviewcode.md command explicitly specifies "Save: docs/reviews/<task-id>.review.md" as a required step. Skipping it and waiting for the user to notice is a failure to follow the command spec.

**How to apply:** Immediately after generating the review verdict, write the file — never skip, never wait for user confirmation. Naming convention: `docs/reviews/<feature>.<story>-<task>.review.md`.

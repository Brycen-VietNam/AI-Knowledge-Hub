# COLD Memory Archive
# Features moved here when status = DONE.
# Never auto-loaded. Access via: /context <feature> --from-cold

---

## How to archive
Triggered automatically by `/report` when feature is APPROVED. Manual steps:
  1. Move `WARM/<feature>.mem.md` → `COLD/<feature>.archive.md`
  2. Add one row to Archive Index below
  3. Update `HOT.md` — remove from In Progress, clear blockers if applicable

---

## Archive Index

| Feature | Completed | Stories | Tests | Unblocks | Report |
|---------|-----------|---------|-------|----------|--------|
| <!-- feature slug --> | <!-- YYYY-MM-DD --> | <!-- S001–SNNN --> | <!-- N/N --> | <!-- comma-separated --> | <!-- docs/reports/....report.md --> |

<!-- Add one row per completed feature. Remove the template row above on first real entry. -->

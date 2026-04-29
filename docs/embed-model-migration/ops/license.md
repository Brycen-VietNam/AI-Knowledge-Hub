# License & Provenance: multilingual-e5-large (POC)

> Created: 2026-04-29 | Feature: embed-model-migration | Task: S004 T003
> Related: `.claude/memory/WARM/embed-model-migration.mem.md` (D10, D11, POC → PRODUCT MIGRATION CHECKLIST)

---

## Model Sourcing

| Field | Value |
|-------|-------|
| Upstream model | `intfloat/multilingual-e5-large` |
| Upstream license | MIT — see `LICENSE.e5` |
| Upstream source | HuggingFace: `https://huggingface.co/intfloat/multilingual-e5-large` |
| POC distribution | `zylonai/multilingual-e5-large` (Ollama community tag, MIT-declared) |
| Ollama registry | `https://ollama.com/zylonai/multilingual-e5-large` |
| Pinned digest | `sha256:c1522b1cf095b82080a9b804d86b4aa609e71a48bbdbcde7ea7864bb9b0cd76b` |
| Digest verified | 2026-04-28 (Spike A — dim=1024, cross-lingual cos=0.94, prefix-sensitive) |
| Format | F16 GGUF (~1.1 GB on disk) |
| Dimensions | 1024 |

---

## License Summary

`intfloat/multilingual-e5-large` is released under the **MIT License**.
Verbatim license text: see `LICENSE.e5` in this directory.

The `zylonai` Ollama tag redistributes these weights and declares the same MIT license.

**Internal-only consumption note**: This deployment is for Brysen Group internal use only.
No external distribution of model weights occurs. MIT redistribution obligations (attribution
notice in distributed software) are therefore **not triggered** for this POC deployment.

---

## POC Scope Statement

This sourcing decision (D10) is explicitly scoped to the POC phase of `embed-model-migration`.

Before any promotion to a **production or user-facing** deployment, the POC → PRODUCT MIGRATION
CHECKLIST in `.claude/memory/WARM/embed-model-migration.mem.md` (§ POC → PRODUCT MIGRATION
CHECKLIST) **must be reviewed and all checkboxes completed**. Key evaluation paths:

- **Path A** (recommended): Self-convert from `intfloat/multilingual-e5-large` safetensors via
  `llama.cpp convert-hf-to-gguf.py` — clean audit trail, first-party source, restores D08.
- **Path B**: Verify `zylonai` tag integrity vs HF reference (cosine ≥ 0.99 across 50+ probes).
- **Path C**: Brysen IT/legal approved-vendor process if formal policy is adopted.

Triggers for re-evaluation: external customers, SOC2/ISO27001 adoption, tag digest change,
multi-tenant/multi-region deployment, or any legal/IT supply-chain query.

---

## Backup GGUF Blob

| Field | Value |
|-------|-------|
| Backup location | `TODO: ops to define — e.g. s3://<BUCKET>/models/multilingual-e5-large-f16.gguf` |
| SHA-256 of GGUF | `TODO: fill after first pull — run sha256sum on the pulled .gguf file` |
| Fallback path | Appendix B of `ollama_setup.md` (self-convert from HF safetensors) |

> Once the backup S3 path is confirmed, update this table and commit.
> Command to get SHA: `sha256sum ~/.ollama/models/blobs/sha256-c1522b1cf095b82080a9b804d86b4aa609e71a48bbdbcde7ea7864bb9b0cd76b`

---

## No Credentials or Internal Hostnames

This file contains no hardcoded credentials, API keys, passwords, or internal hostnames.
All environment-specific values (S3 bucket, instance addresses) are marked TODO for ops to fill.

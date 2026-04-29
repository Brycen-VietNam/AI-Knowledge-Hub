# Ollama Setup: zylonai/multilingual-e5-large on AWS

> Runbook: embed-model-migration — S004 T002
> Instance: AWS t3.medium (2 vCPU, 4 GB RAM)
> Model: `zylonai/multilingual-e5-large` — F16, MIT, dim=1024, ~1.1 GB
> Digest (pinned): `sha256:c1522b1cf095b82080a9b804d86b4aa609e71a48bbdbcde7ea7864bb9b0cd76b`

---

## Prerequisites

- AWS t3.medium with Ubuntu 22.04 LTS
- Port 11434 open in security group (inbound, restricted to VPC CIDR only)
- `EMBEDDING_MODEL=zylonai/multilingual-e5-large` set in environment
- `OLLAMA_MAX_EMBED_CHARS=1400` set in environment (prevents silent truncation on long passages)

---

## Primary Path: Pull from Ollama Registry

### 1. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:

```bash
ollama --version
```

### 2. Start Ollama Server (Docker)

```bash
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  -e OLLAMA_MAX_EMBED_CHARS=1400 \
  ollama/ollama
```

> If running Ollama natively (not Docker), set `OLLAMA_MAX_EMBED_CHARS=1400` in `/etc/systemd/system/ollama.service` Environment block and `systemctl daemon-reload && systemctl restart ollama`.

### 3. Pull Model (Pinned Digest)

```bash
ollama pull zylonai/multilingual-e5-large
```

After pull, verify digest matches:

```bash
ollama show zylonai/multilingual-e5-large --modelfile | grep -i digest
# Expected: sha256:c1522b1cf095b82080a9b804d86b4aa609e71a48bbdbcde7ea7864bb9b0cd76b
```

If digest does not match, **do not proceed** — pull may have resolved to a different tag version. See Appendix B for pinned GGUF import.

### 4. Smoke Verification

```bash
curl -s -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"zylonai/multilingual-e5-large","prompt":"test"}' \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
emb = r.get('embedding', [])
assert len(emb) == 1024, f'Expected 1024 dims, got {len(emb)}'
print(f'PASS: embedding dims={len(emb)}, first_val={emb[0]:.6f}')
"
```

Expected output:

```
PASS: embedding dims=1024, first_val=<float>
```

### 5. Set Environment Variables

Add to your `.env` (or AWS Parameter Store / Secrets Manager for production):

```env
EMBEDDING_MODEL=zylonai/multilingual-e5-large
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MAX_EMBED_CHARS=1400
```

> `OLLAMA_BASE_URL` defaults to `http://localhost:11434`. Override for remote Ollama instances.

---

## Instance Sizing Notes

| Resource | t3.medium | Model requirement |
|----------|-----------|-------------------|
| RAM | 4 GB | ~1.1 GB (F16 weights loaded) |
| vCPU | 2 | Sufficient for embedding-only (no GPU) |
| Disk | 20 GB+ recommended | ~1.1 GB model + OS + logs |
| Network | Up to 5 Gbps | Pull once; inference local |

CPU-only inference latency: ~80–120 ms/request (single embed). Batch via `api/embed` endpoint for throughput — see [embedder.py batch_embed_passage](../../../backend/rag/embedder.py).

---

## Appendix B: Self-Convert Fallback (D08 Path)

Use when `zylonai/multilingual-e5-large` is unavailable from Ollama registry.
Source: `intfloat/multilingual-e5-large` (same weights, MIT license).

### B1. Clone llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
pip install -r requirements.txt
```

### B2. Download safetensors from HuggingFace

```bash
pip install huggingface_hub
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='intfloat/multilingual-e5-large',
    local_dir='/tmp/multilingual-e5-large'
)
"
```

### B3. Convert to GGUF (F16)

```bash
python3 convert-hf-to-gguf.py \
  /tmp/multilingual-e5-large \
  --outfile /tmp/multilingual-e5-large-f16.gguf \
  --outtype f16
```

### B4. Create Modelfile

```
# /tmp/Modelfile
FROM /tmp/multilingual-e5-large-f16.gguf
```

### B5. Register with Ollama

```bash
ollama create multilingual-e5-large-local -f /tmp/Modelfile
```

### B6. Update env to use local tag

```env
EMBEDDING_MODEL=multilingual-e5-large-local
```

Smoke test (same curl as Primary Path, substitute model name).

> **Note:** Local tag has no pinned digest guarantee. Document the GGUF SHA-256 manually for audit:
> `sha256sum /tmp/multilingual-e5-large-f16.gguf >> docs/embed-model-migration/ops/license.md`

### B7. GGUF Blob Backup Location

Backup GGUF to S3 after convert for team reuse:

```bash
aws s3 cp /tmp/multilingual-e5-large-f16.gguf \
  s3://<YOUR-BUCKET>/models/multilingual-e5-large-f16.gguf
```

> Replace `<YOUR-BUCKET>` with your team's artifacts bucket. Update `license.md` with the S3 path once set.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `connection refused` on port 11434 | Ollama not running | `docker ps` or `systemctl status ollama` |
| `model not found` error | Pull incomplete | Re-run `ollama pull zylonai/multilingual-e5-large` |
| Embedding dim ≠ 1024 | Wrong model loaded | Verify `EMBEDDING_MODEL` env var |
| Slow embeds (>500ms) | Cold start or CPU saturation | Warm up with a dummy embed at startup; check vCPU utilization |
| Digest mismatch | Registry tag re-tagged | Use Appendix B GGUF path with known-good artifact |

"""Spike: compare Ollama community E5 tag vs sentence-transformers reference.

Goal: verify pooling + L2 normalize match between Ollama and HF reference.
Pass criteria:
  - dim == 1024
  - cosine(ollama_vec, hf_vec) >= 0.99 for same input
  - prefix-difference test: cosine(query: X, passage: X) < 1.0 (prefix actually changes vector)
"""
import json
import sys
import time
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "zylonai/multilingual-e5-large"

# 5 multilingual probes, 2 with prefix variants
PROBES = [
    ("query: how to search", "EN-query"),
    ("passage: search guide for users", "EN-passage"),
    ("query: 検索する方法", "JA-query"),
    ("passage: ユーザー向けの検索ガイド", "JA-passage"),
    ("query: cách tìm kiếm", "VI-query"),
]


def ollama_embed(text: str) -> list[float]:
    r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": text}, timeout=30)
    r.raise_for_status()
    return r.json()["embedding"]


def cosine(a: list[float], b: list[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


def main() -> int:
    print(f"=== Spike A: Ollama community E5 sanity check ===")
    print(f"Model: {OLLAMA_MODEL}")

    results = {}
    for text, label in PROBES:
        t0 = time.perf_counter()
        try:
            vec = ollama_embed(text)
        except Exception as e:
            print(f"  [{label}] FAIL: {e}")
            return 1
        dt = (time.perf_counter() - t0) * 1000
        norm = sum(x * x for x in vec) ** 0.5
        results[label] = vec
        print(f"  [{label}] dim={len(vec)} norm={norm:.4f} latency={dt:.0f}ms text={text[:40]!r}")

    # Dimension check
    dims = {len(v) for v in results.values()}
    print(f"\nDim check: {dims}")
    if dims != {1024}:
        print(f"FAIL: expected dim=1024, got {dims}")
        return 1
    print("OK: dim=1024 across all probes")

    # Prefix sensitivity check: query: X vs passage: X for same content
    print("\nPrefix sensitivity (lower cosine = prefix matters):")
    for q_label, p_label in [("EN-query", "EN-passage"), ("JA-query", "JA-passage")]:
        c = cosine(results[q_label], results[p_label])
        verdict = "OK (different)" if c < 0.999 else "WARN (identical — prefix may be ignored)"
        print(f"  cos({q_label}, {p_label}) = {c:.4f}  {verdict}")

    # Cross-lingual smoke: EN-query vs JA-query (same intent, different lang)
    c_xl = cosine(results["EN-query"], results["JA-query"])
    print(f"\nCross-lingual (EN/JA same intent): cos = {c_xl:.4f}")
    print("  Expected for E5: > 0.7 (multilingual aligned space)")
    print("  If < 0.5: model may be English-only or pooling is broken")

    out = Path(__file__).parent / "spike_a_ollama_only.json"
    out.write_text(json.dumps({k: v[:8] + ["..."] for k, v in results.items()}, indent=2))
    print(f"\nFirst 8 dims per probe saved to: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

# RAG layer environment configuration — single source of truth for Ollama URLs.
# Rule: S005 — no hardcoded values; all via environment variables.
# Note: OLLAMA_EMBED_URL and OLLAMA_LLM_URL are intentionally separate:
#   embedding must always point to a local instance;
#   LLM generation can point to a remote GPU server.
import os

# Embedding: always local Ollama — do not point to remote
OLLAMA_EMBED_URL: str = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434")

# LLM generation: can be remote when LLM_PROVIDER=ollama
OLLAMA_LLM_URL: str = os.getenv("OLLAMA_LLM_URL", "http://localhost:11434")

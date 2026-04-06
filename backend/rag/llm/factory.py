import os
import threading

from .base import LLMProvider
from .exceptions import LLMError


class LLMProviderFactory:
    # Spec: docs/llm-provider/spec/llm-provider.spec.md#S003
    # Task: T009 — Singleton factory (D05 pattern from TokenizerFactory)
    # Decision: D01 — Ollama default; D05 — singleton per provider name
    _instances: dict[str, LLMProvider] = {}
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get(cls) -> LLMProvider:
        provider_name = os.getenv("LLM_PROVIDER", "ollama")
        if provider_name in cls._instances:
            return cls._instances[provider_name]
        with cls._lock:
            if provider_name not in cls._instances:
                cls._instances[provider_name] = cls._create(provider_name)
        return cls._instances[provider_name]

    @classmethod
    def reset(cls) -> None:
        """Clear all cached singleton instances. Intended for use in tests only."""
        with cls._lock:
            cls._instances.clear()

    @classmethod
    def _create(cls, name: str) -> LLMProvider:
        if name == "ollama":
            from .ollama import OllamaAdapter
            return OllamaAdapter()
        if name == "openai":
            from .openai import OpenAIAdapter
            return OpenAIAdapter()
        if name == "claude":
            from .claude import ClaudeAdapter
            return ClaudeAdapter()
        raise LLMError(f"Unsupported provider: {name!r}. Supported: ollama, openai, claude")

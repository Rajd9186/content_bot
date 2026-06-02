from __future__ import annotations

TASK_PROFILES: dict[str, dict[str, list[str]]] = {
    "research": {
        "preferred": ["nvidia", "groq"],
        "fallback": ["groq", "ollama"],
        "fast_preferred": ["groq"],
        "fast_fallback": ["ollama"],
    },
    "planner": {
        "preferred": ["groq", "nvidia"],
        "fallback": ["nvidia", "ollama"],
        "fast_preferred": ["groq"],
        "fast_fallback": ["ollama"],
    },
    "writer": {
        "preferred": ["ollama", "groq"],
        "fallback": ["nvidia", "groq"],
        "fast_preferred": ["ollama"],
        "fast_fallback": ["groq"],
    },
    "seo": {
        "preferred": ["openai", "nvidia"],
        "fallback": ["groq", "ollama"],
        "fast_preferred": ["groq"],
        "fast_fallback": ["ollama"],
    },
    "fact_checker": {
        "preferred": ["nvidia", "groq"],
        "fallback": ["openai", "ollama"],
        "fast_preferred": ["nvidia"],
        "fast_fallback": ["ollama"],
    },
    "compliance": {
        "preferred": ["openai", "nvidia"],
        "fallback": ["groq", "ollama"],
        "fast_preferred": ["groq"],
        "fast_fallback": ["ollama"],
    },
    "finalizer": {
        "preferred": ["groq", "nvidia"],
        "fallback": ["openai", "ollama"],
        "fast_preferred": ["groq"],
        "fast_fallback": ["ollama"],
    },
}

TASK_COMPLEXITY: dict[str, str] = {
    "research": "medium",
    "planner": "fast",
    "writer": "heavy",
    "seo": "fast",
    "fact_checker": "heavy",
    "compliance": "medium",
    "finalizer": "fast",
    "memory_retrieval": "fast",
    "skill_retrieval": "fast",
}

PROVIDER_LIMITS: dict[str, dict[str, int]] = {
    "groq": {"rpm": 30, "tpm": 12000, "max_concurrent": 10},
    "nvidia": {"rpm": 500, "tpm": 500000, "max_concurrent": 20},
    "openai": {"rpm": 500, "tpm": 1000000, "max_concurrent": 50},
    "ollama": {"rpm": 1000, "tpm": 1000000, "max_concurrent": 30},
    "anthropic": {"rpm": 50, "tpm": 100000, "max_concurrent": 10},
}

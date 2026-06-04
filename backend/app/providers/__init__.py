import os
from typing import Optional

from app.config import settings
from app.providers.base.llm_provider import BaseLLMProvider
from app.log_config.logger import get_logger

logger = get_logger(__name__)

_llm_client: Optional[BaseLLMProvider] = None

try:
    from app.providers.groq.provider import GroqProvider as _GroqProvider
    _HAS_GROQ = True
except ImportError:
    _HAS_GROQ = False

try:
    from app.providers.openai.provider import OpenAIProvider as _OpenAIProvider
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


def get_llm_client() -> BaseLLMProvider:
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
    openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")

    if groq_key and _HAS_GROQ:
        logger.info("Using Groq LLM provider")
        from app.providers.groq.provider import GroqProvider
        _llm_client = GroqProvider(
            model=settings.groq_model or "llama-3.3-70b-versatile",
            api_key=groq_key,
        )
    elif openai_key and _HAS_OPENAI:
        logger.info("Using OpenAI LLM provider")
        from app.providers.openai.provider import OpenAIProvider
        _llm_client = OpenAIProvider(
            model=settings.openai_model or "gpt-4o",
            api_key=openai_key,
        )
    elif _HAS_GROQ:
        logger.warning("No API key found, using Groq with empty key")
        from app.providers.groq.provider import GroqProvider
        _llm_client = GroqProvider(api_key="")
    elif _HAS_OPENAI:
        logger.warning("No API key found, using OpenAI with empty key")
        from app.providers.openai.provider import OpenAIProvider
        _llm_client = OpenAIProvider(api_key="")
    else:
        raise RuntimeError("No LLM provider available (install openai or groq package)")

    return _llm_client

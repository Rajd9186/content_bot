import os
import json
from abc import ABC, abstractmethod
from typing import Any

from ollama import AsyncClient as OllamaAsyncClient, ResponseError
from groq import AsyncGroq

from app.config import settings
from app.log_config.logger import get_logger
from app.utils.retry import async_retry


class BaseAgent(ABC):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # Determine which provider to use - check settings and environment directly as fallback
        groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.use_groq = bool(groq_key)
        
        if self.use_groq:
            self.groq_client = AsyncGroq(api_key=groq_key)
            self.model = settings.groq_model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            self.logger.info(f"Initialized with Groq provider using model {self.model}")
        else:
            self.logger.info(f"Groq API key not found (len={len(groq_key)}). Falling back to Ollama.")
            headers = {}
            if settings.ollama_api_key:
                headers["Authorization"] = f"Bearer {settings.ollama_api_key}"
            self.ollama_client = OllamaAsyncClient(
                host=settings.ollama_base_url,
                headers=headers,
            )
            self.model = settings.ollama_model
            self.logger.info(f"Initialized with Ollama provider using model {self.model}")

    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def parse_response(self, response: str) -> Any:
        ...

    @async_retry(max_retries=settings.max_retries, delay=settings.retry_delay)
    async def call_llm(self, messages: list[dict], temperature: float = 0.3) -> str:
        self.logger.info(
            "Calling LLM",
            extra={"model": self.model, "messages_count": len(messages), "provider": "Groq" if self.use_groq else "Ollama"},
        )
        
        if self.use_groq:
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            content = response.choices[0].message.content
        else:
            response = await self.ollama_client.chat(
                model=self.model,
                messages=messages,
            )
            content = response["message"]["content"]
            
        self.logger.info("LLM response received")
        return content

    async def run(self, **kwargs) -> Any:
        system = self.system_prompt()
        user_content = self.build_user_prompt(**kwargs)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        try:
            raw_response = await self.call_llm(messages)
            return self.parse_response(raw_response)
        except (ResponseError, Exception) as e:
            self.logger.warning(
                "LLM call failed, caller should handle fallback",
                extra={"error": str(e), "agent": self.__class__.__name__},
            )
            raise

    def build_user_prompt(self, **kwargs) -> str:
        parts = []
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, (list, dict)):
                    parts.append(f"{key}:\n{json.dumps(value, indent=2)}")
                else:
                    parts.append(f"{key}: {value}")
        return "\n\n".join(parts)

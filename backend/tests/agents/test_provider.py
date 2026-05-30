from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.provider.base import BaseProvider, ProviderRequest, ProviderResponse
from app.agents.provider.factory import ProviderFactory
from app.agents.provider.openai import OpenAIProvider
from app.agents.provider.anthropic import AnthropicProvider
from app.agents.provider.groq import GroqProvider
from app.agents.provider.local import LocalProvider


def test_base_provider_abstract() -> None:
    # Cannot instantiate abstract class
    with pytest.raises(TypeError):
        BaseProvider("test")  # type: ignore


def test_provider_request_creation() -> None:
    request = ProviderRequest(
        model="gpt-4",
        system_prompt="You are a helpful assistant",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
        max_tokens=1000
    )
    assert request.model == "gpt-4"
    assert request.system_prompt == "You are a helpful assistant"
    assert len(request.messages) == 1
    assert request.temperature == 0.7
    assert request.max_tokens == 1000


def test_provider_response_defaults() -> None:
    response = ProviderResponse()
    assert response.content == ""
    assert response.success is False
    assert response.error is None
    assert response.provider == ""
    assert response.model == ""


def test_provider_factory_registration() -> None:
    factory = ProviderFactory()
    mock_provider = OpenAIProvider()
    
    factory.register("test_provider", mock_provider)
    retrieved = factory.get("test_provider")
    
    assert retrieved is mock_provider


def test_provider_factory_get_or_create_new() -> None:
    factory = ProviderFactory()
    provider = factory.get_or_create("openai", "gpt-4")
    
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-4"


def test_provider_factory_get_or_create_existing() -> None:
    factory = ProviderFactory()
    provider1 = factory.get_or_create("anthropic", "claude-2")
    provider2 = factory.get_or_create("anthropic", "claude-3")
    
    # Should return the same instance
    assert provider1 is provider2
    # Should keep the first model
    assert provider1.model == "claude-2"


def test_provider_factory_auto_create_by_name() -> None:
    factory = ProviderFactory()
    
    openai = factory.get_or_create("openai")
    assert isinstance(openai, OpenAIProvider)
    
    anthropic = factory.get_or_create("anthropic")
    assert isinstance(anthropic, AnthropicProvider)
    
    groq = factory.get_or_create("groq")
    assert isinstance(groq, GroqProvider)
    
    local = factory.get_or_create("local")
    assert isinstance(local, LocalProvider)


@patch("app.agents.provider.openai.aiohttp.ClientSession")
async def test_openai_provider_execute_success(mock_session_class) -> None:
    # Mock the HTTP response
    class MockResponse:
        status = 200
        async def json(self):
            return {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            }
    
    class MockPost:
        async def __aenter__(self):
            return MockResponse()
        async def __aexit__(self, *args):
            pass
    
    class MockClientSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        def post(self, *args, **kwargs):
            return MockPost()
    
    mock_session_class.return_value = MockClientSession()
    
    provider = OpenAIProvider("gpt-4")
    request = ProviderRequest(model="gpt-4", messages=[{"role": "user", "content": "Hello"}])
    
    response = await provider.execute(request)
    
    assert response.success is True
    assert response.content == "Test response"
    assert response.token_usage.total_tokens == 30


@patch("app.agents.provider.openai.aiohttp.ClientSession")
async def test_openai_provider_execute_http_error(mock_session_class) -> None:
    class MockErrorResponse:
        status = 401
        async def json(self):
            return {"error": {"message": "Invalid API key"}}
    
    class MockPost:
        async def __aenter__(self):
            return MockErrorResponse()
        async def __aexit__(self, *args):
            pass
    
    class MockClientSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        def post(self, *args, **kwargs):
            return MockPost()
    
    mock_session_class.return_value = MockClientSession()
    
    provider = OpenAIProvider()
    request = ProviderRequest(model="gpt-4", messages=[{"role": "user", "content": "Hello"}])
    
    response = await provider.execute(request)
    
    assert response.success is False
    assert "Invalid API key" in response.error  # type: ignore


async def test_base_provider_execute_with_retry_success_immediately() -> None:
    provider = OpenAIProvider()
    provider.execute = AsyncMock(return_value=ProviderResponse(  # type: ignore
        success=True, content="Success", provider="openai", model="gpt-4"
    ))
    
    request = ProviderRequest(model="gpt-4")
    response = await provider.execute_with_retry(request, max_retries=2)
    
    assert response.success is True
    assert provider.execute.call_count == 1  # No retries needed


async def test_base_provider_execute_with_retry_eventual_success() -> None:
    provider = OpenAIProvider()
    
    # First call fails, second succeeds
    provider.execute = AsyncMock(side_effect=[  # type: ignore
        ProviderResponse(success=False, error="Temporary error", provider="openai", model="gpt-4"),
        ProviderResponse(success=True, content="Success", provider="openai", model="gpt-4")
    ])
    
    request = ProviderRequest(model="gpt-4")
    response = await provider.execute_with_retry(request, max_retries=2)
    
    assert response.success is True
    assert response.content == "Success"
    assert provider.execute.call_count == 2  # One retry


async def test_base_provider_execute_with_retry_all_failures() -> None:
    provider = OpenAIProvider()
    provider.execute = AsyncMock(return_value=ProviderResponse(  # type: ignore
        success=False, error="Persistent error", provider="openai", model="gpt-4"
    ))
    
    request = ProviderRequest(model="gpt-4")
    response = await provider.execute_with_retry(request, max_retries=2)
    
    assert response.success is False
    assert response.error == "All 3 retries failed: Persistent error"
    assert provider.execute.call_count == 3  # Initial + 2 retries

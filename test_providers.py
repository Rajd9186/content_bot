from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.agents.provider.factory import ProviderFactory
from app.agents.provider.base import ProviderRequest


async def test_provider(name: str, model: str, api_key: str | None) -> dict:
    print(f"\n{'='*60}")
    print(f"Testing {name} (model: {model})")
    print(f"{'='*60}")

    if not api_key:
        print(f"  [SKIP] No API key set")
        return {"status": "skipped", "reason": "no_api_key"}

    try:
        factory = ProviderFactory()
        provider = factory.get_or_create(name, model)

        request = ProviderRequest(
            model=model,
            system_prompt="You are a helpful assistant. Keep responses brief.",
            messages=[{"role": "user", "content": "Say 'Hello from {name}' in exactly those words."}],
            temperature=0.1,
            max_tokens=50,
            timeout_ms=30000,
        )

        print(f"  [INFO] Making request to {name}...")
        response = await provider.execute(request)

        if response.success:
            print(f"  [SUCCESS] Response received!")
            print(f"  [INFO] Content: {response.content[:200]}")
            print(f"  [INFO] Token usage: {response.token_usage}")
            print(f"  [INFO] Latency: {getattr(response, 'latency_ms', 'N/A')}ms")
            return {
                "status": "success",
                "content": response.content,
                "token_usage": response.token_usage,
            }
        else:
            print(f"  [FAIL] Error: {response.error}")
            return {"status": "fail", "error": response.error}

    except Exception as e:
        print(f"  [ERROR] Exception: {type(e).__name__}: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    print("Testing Groq and NVIDIA LLM Providers")
    print("=" * 60)

    groq_key = os.environ.get("GROQ_API_KEY")
    nvidia_key = os.environ.get("NVIDIA_API_KEY")

    groq_result = await test_provider("groq", "llama-3.3-70b-versatile", groq_key)
    nvidia_result = await test_provider("nvidia", "nvidia/nemotron-3-super-120b-a12b", nvidia_key)
    nvidia_llama_result = await test_provider("nvidia", "meta/llama-3.1-70b-instruct", nvidia_key)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Groq:           {groq_result['status'].upper()}")
    print(f"NVIDIA nemotron: {nvidia_result['status'].upper()}")
    print(f"NVIDIA llama:   {nvidia_llama_result['status'].upper()}")

    all_passed = (
        groq_result["status"] == "success" and
        nvidia_result["status"] == "success" and
        nvidia_llama_result["status"] == "success"
    )
    print(f"\nOverall: {'ALL PROVIDERS WORKING' if all_passed else 'SOME PROVIDERS FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
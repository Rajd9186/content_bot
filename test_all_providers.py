from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.agents.provider.factory import ProviderFactory
from app.agents.provider.base import ProviderRequest


async def test_provider(name: str, model: str) -> dict:
    try:
        factory = ProviderFactory()
        provider = factory.get_or_create(name, model)

        request = ProviderRequest(
            model=model,
            system_prompt="You are a helpful assistant. Keep responses brief.",
            messages=[{"role": "user", "content": "Say 'Hello from assistant' in exactly those words."}],
            temperature=0.1,
            max_tokens=50,
            timeout_ms=30000,
        )

        response = await provider.execute(request)

        if response.success:
            latency = getattr(response, "latency_ms", None) or 0
            print(f"  {name}/{model}: OK — {latency:.0f}ms")
            return {"status": "success", "latency_ms": latency}
        else:
            print(f"  {name}/{model}: FAIL — {response.error}")
            return {"status": "fail", "error": response.error}

    except Exception as e:
        print(f"  {name}/{model}: ERROR — {type(e).__name__}: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    results = {}

    print("=" * 60)
    print("TESTING ALL CONFIGURED LLM PROVIDERS")
    print("=" * 60)

    # Groq
    if os.environ.get("GROQ_API_KEY"):
        results["groq:llama-3.3-70b-versatile"] = await test_provider("groq", "llama-3.3-70b-versatile")
        results["groq:mixtral-8x7b"] = await test_provider("groq", "mixtral-8x7b-32k")
    else:
        print("  groq: NOT CONFIGURED (no GROQ_API_KEY)")

    # NVIDIA
    if os.environ.get("NVIDIA_API_KEY"):
        results["nvidia:nemotron-3-super-120b-a12b"] = await test_provider("nvidia", "nvidia/nemotron-3-super-120b-a12b")
        results["nvidia:llama-3.1-70b-instruct"] = await test_provider("nvidia", "meta/llama-3.1-70b-instruct")
        results["nvidia:llama-3.3-70b"] = await test_provider("nvidia", "meta/llama-3.3-70b-instruct")
    else:
        print("  nvidia: NOT CONFIGURED (no NVIDIA_API_KEY)")

    # Ollama
    if os.environ.get("OLLAMA_API_KEY"):
        results["ollama:llama3.2"] = await test_provider("ollama", "llama3.2")
        results["ollama:gpt-oss:120b"] = await test_provider("ollama", "gpt-oss:120b")
        results["ollama:mixtral"] = await test_provider("ollama", "mixtral")
    else:
        print("  ollama: NOT CONFIGURED (no OLLAMA_API_KEY)")

    # OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        results["openai:gpt-4o"] = await test_provider("openai", "gpt-4o")
        results["openai:gpt-4o-mini"] = await test_provider("openai", "gpt-4o-mini")
    else:
        print("  openai: NOT CONFIGURED (no OPENAI_API_KEY)")

    # Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        results["anthropic:claude-sonnet-4"] = await test_provider("anthropic", "claude-sonnet-4-20250514")
        results["anthropic:claude-3-5-sonnet"] = await test_provider("anthropic", "claude-3-5-sonnet-20250620")
    else:
        print("  anthropic: NOT CONFIGURED (no ANTHROPIC_API_KEY)")

    # Summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    for key, result in results.items():
        status = result["status"].upper()
        latency = f"{result.get('latency_ms', 0):.0f}ms" if result["status"] == "success" else result.get("error", "")[:40]
        print(f"  {status:8} {key:45} {latency}")

    passed = sum(1 for r in results.values() if r["status"] == "success")
    total = len(results)
    print(f"\n  {passed}/{total} providers working")
    print(f"  Overall: {'ALL PASS' if passed == total else 'SOME FAILURES'}")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(min(exit_code, 1))
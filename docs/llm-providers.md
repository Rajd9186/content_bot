# LLM Provider Architecture

The platform uses an abstracted LLM provider system that supports multiple backends (Groq, NVIDIA, OpenAI, Anthropic, Ollama, Local) with automatic failover, circuit breakers, and rate limiting.

## Architecture Overview

```
Agent Pipeline
     │
     ▼
ProviderRouter / Adapter
     │
     ▼
ProviderFactory ──► BaseProvider (abstract)
     │                   │
     │          ┌────────┼────────┐
     │          ▼        ▼        ▼
     │       Groq   NVIDIA    OpenAI
     │    Provider Provider  Provider
     │
     ▼
ProviderFailover (circuit breakers + TPM tracking)
     │
     ▼
Redis (TPM budget tracking across workers)
```

## Provider System

### Base Interface

All providers implement `BaseProvider` from `app.agents.provider.base`:

```python
class BaseProvider(ABC):
    @property
    def name(self) -> str
    @property
    def model(self) -> str

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        """Make a single LLM API call."""

    async def execute_with_retry(self, request, max_retries=3) -> ProviderResponse:
        """Retry with exponential backoff on failure."""
```

### ProviderRequest / ProviderResponse

```python
@dataclass
class ProviderRequest:
    model: str
    system_prompt: str | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_ms: int = 60000
    stop_sequences: list[str] | None = None

@dataclass
class ProviderResponse:
    content: str = ""
    token_usage: TokenUsage
    latency_ms: float = 0.0
    success: bool = False
    error: str | None = None
    provider: str = ""
    model: str = ""
    raw_response: Any | None = None
```

### Provider Factory

The `ProviderFactory` (`app.agents.provider.factory`) creates provider instances by name:

```python
from app.agents.provider.factory import provider_factory

# Get or create singleton instance
provider = provider_factory.get_or_create("groq", "llama-3.3-70b-versatile")

# Make a call
response = await provider.execute(request)
```

Supported provider name aliases:
| Provider | Aliases |
|----------|---------|
| OpenAI | `openai`, `gpt-4o`, `gpt-4`, `gpt-3.5` |
| Anthropic | `anthropic`, `claude`, `claude-sonnet`, `claude-opus` |
| Groq | `groq`, `llama`, `mixtral` |
| NVIDIA | `nvidia`, `nemotron` |
| Ollama | `ollama`, `gpt-oss` |
| Local | `local`, `llamacpp` |

## Provider Implementations

### Groq (`app.agents.provider.groq.GroqProvider`)

- **API**: OpenAI-compatible (`https://api.groq.com/openai/v1/chat/completions`)
- **Default Model**: `llama-3.3-70b-versatile`
- **Supported Models**: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b`
- **Context Limit**: 8,192 tokens (provider-level)
- **Rate Limit**: 12,000 TPM (enforced via Redis)
- **API Key**: `GROQ_API_KEY`

### NVIDIA (`app.agents.provider.nvidia.NvidiaProvider`)

- **API**: NVIDIA NIM (`https://integrate.api.nvidia.com/v1/chat/completions`)
- **Default Model**: `nvidia/nemotron-3-super-120b-a12b`
- **Recommended Models**:
  - `nvidia/nemotron-3-super-120b-a12b` (large, ~8.7s latency)
  - `meta/llama-3.1-70b-instruct` (fast, ~500ms latency)
- **Context Limit**: 4,096 tokens
- **API Key**: `NVIDIA_API_KEY`

### OpenAI (`app.agents.provider.openai.OpenAIProvider`)

- **API**: OpenAI (`https://api.openai.com/v1/chat/completions`)
- **Default Model**: `gpt-4o`
- **Context Limit**: 128,000 tokens
- **API Key**: `OPENAI_API_KEY`

### Anthropic (`app.agents.provider.anthropic.AnthropicProvider`)

- **API**: Anthropic (`https://api.anthropic.com/v1/messages`)
- **Default Model**: `claude-sonnet-4-20250514`
- **API Key**: `ANTHROPIC_API_KEY`

### Ollama (`app.agents.provider.ollama.OllamaProvider`)

- **API**: Ollama (`http://localhost:11434/api/chat`)
- **Default Model**: `llama3.2`
- **API Key**: `OLLAMA_API_KEY` (if required)

### Local (`app.agents.provider.local.LocalProvider`)

- **Use Case**: Custom/local model endpoints
- **API Key**: `LOCAL_API_KEY`

## Agent-to-Provider Routing

Each agent type has a preferred provider assignment in `app.infrastructure.failover.provider_failover`:

| Agent | Primary Provider | Failover Chain |
|-------|-----------------|----------------|
| `research` | OpenAI | OpenAI → NVIDIA → Groq → Ollama |
| `planner` | OpenAI | OpenAI → NVIDIA → Groq → Ollama |
| `writer` | Groq | Groq → NVIDIA → OpenAI → Ollama |
| `seo` | OpenAI | OpenAI → NVIDIA → Groq → Ollama |
| `fact_checker` | OpenAI | OpenAI → NVIDIA → Groq → Ollama |
| `compliance` | OpenAI | OpenAI → NVIDIA → Groq → Ollama |
| `finalizer` | Groq | Groq → NVIDIA → OpenAI → Ollama |

The `ProviderFailover.select_provider()` picks the first available provider from the chain.

## Reliability Features

### Circuit Breaker

Each provider has a circuit breaker that opens after 5 consecutive failures. When open, the provider is skipped for 60 seconds before entering half-open state.

```
CLOSED (normal) ──[5 failures]──► OPEN (blocked)
    ▲                                  │
    │                           [60s elapsed]
    │                                  ▼
    └──────[success]────── HALF_OPEN (test requests)
```

```python
from app.infrastructure.failover.provider_failover import provider_failover

# Check circuit state
state = provider_failover.circuit_states
# {'openai': 'closed', 'nvidia': 'open', 'groq': 'closed', 'ollama': 'closed'}
```

### Redis-Based TPM Tracking

Groq has a 12,000 TPM limit shared across all workers. The `ProviderFailover.acquire_tpm_budget()` method uses Redis to track token usage per 60-second window:

```python
await provider_failover.acquire_tpm_budget("groq", estimated_tokens=500)
# Returns False if budget would be exceeded
```

If Redis is unavailable, TPM tracking is bypassed (fail-open).

### Retry with Exponential Backoff

Every provider supports built-in retry via `execute_with_retry()`:

```python
response = await provider.execute_with_retry(request, max_retries=3)
# Retries with delays: 1s, 2s, 4s (capped at 30s)
```

## Context Window Limits

Per-provider context limits enforced by the pipeline context compressor:

```python
PROVIDER_TOKEN_LIMITS = {
    "groq": 8192,
    "nvidia": 4096,
    "openai": 128000,
}
```

The `context_compressor.py` truncates prompts to `PROVIDER_TOKEN_LIMITS[provider] - max_response_tokens` before sending.

## Using Providers in Code

### Direct Factory Usage

```python
from app.agents.provider.factory import provider_factory
from app.agents.provider.base import ProviderRequest

provider = provider_factory.get_or_create("groq", "llama-3.3-70b-versatile")

request = ProviderRequest(
    model="llama-3.3-70b-versatile",
    system_prompt="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.1,
    max_tokens=100,
    timeout_ms=30000,
)

response = await provider.execute(request)
if response.success:
    print(f"Answer: {response.content}")
    print(f"Tokens: {response.token_usage}")
else:
    print(f"Error: {response.error}")
```

### Using ProviderFailover

```python
from app.infrastructure.failover.provider_failover import provider_failover

# Select provider for agent (respects circuit breakers + failover)
provider_name = provider_failover.select_provider("writer", preferred="groq")
provider = provider_factory.get_or_create(provider_name)

response = await provider.execute(request)

if response.success:
    provider_failover.record_success(provider_name)
else:
    provider_failover.record_failure(provider_name)
```

### Via Pipeline Agents

Pipeline agents (ResearchAgent, WriterAgent, etc.) internally use the provider adapter which handles all failover logic automatically. Agents are instantiated as singletons and called through `agent.execute(state)`.

## Adding a New Provider

1. **Create the provider class** in `app/agents/provider/`:

```python
from app.agents.provider.base import BaseProvider, ProviderRequest, ProviderResponse

class MyProvider(BaseProvider):
    def __init__(self, model: str = "my-model") -> None:
        super().__init__("myprovider")
        self._model = model
        self._api_key = os.getenv("MYPROVIDER_API_KEY", "")
        self._base_url = "https://api.myprovider.com/v1"

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        import aiohttp
        # Make HTTP call to your LLM API
        # Return ProviderResponse on success or error
```

2. **Register in ProviderFactory**:

```python
# In factory.py _create() method:
elif normalized in ("myprovider", "my"):
    return MyProvider(model or "my-default-model")
```

3. **Add to failover chain** in `app/infrastructure/failover/provider_failover.py`:

```python
FAILOVER_CHAIN = {
    "research": ["openai", "myprovider", "nvidia", "groq", "ollama"],
    # ...
}

# Add to __init__ circuits dict:
self._circuits["myprovider"] = CircuitBreaker("myprovider")
```

## Environment Variables

```bash
# Required API Keys
GROQ_API_KEY=                    # Groq (https://console.groq.com)
NVIDIA_API_KEY=                  # NVIDIA NIM (https://ngc.nvidia.com)
OPENAI_API_KEY=                  # OpenAI (https://platform.openai.com)
ANTHROPIC_API_KEY=               # Anthropic (https://console.anthropic.com)
OLLAMA_API_KEY=                  # Ollama (if self-hosted requires auth)

# Optional
LOCAL_API_KEY=                   # Local/custom endpoint
```

## Testing Providers

Run the test script from the project root:

```bash
python test_providers.py
```

Expected output:
```
Testing Groq (model: llama-3.3-70b-versatile)
  [SUCCESS] Response received! Latency: ~300ms

Testing NVIDIA (model: nvidia/nemotron-3-super-120b-a12b)
  [SUCCESS] Response received! Latency: ~8000ms

Testing NVIDIA (model: meta/llama-3.1-70b-instruct)
  [SUCCESS] Response received! Latency: ~500ms
```

## Key Files

| File | Purpose |
|------|---------|
| `app/agents/provider/base.py` | `BaseProvider`, `ProviderRequest`, `ProviderResponse` |
| `app/agents/provider/factory.py` | `ProviderFactory` singleton |
| `app/agents/provider/groq.py` | Groq implementation |
| `app/agents/provider/nvidia.py` | NVIDIA NIM implementation |
| `app/agents/provider/openai.py` | OpenAI implementation |
| `app/agents/provider/anthropic.py` | Anthropic implementation |
| `app/agents/provider/ollama.py` | Ollama implementation |
| `app/agents/provider/local.py` | Local/custom endpoint |
| `app/infrastructure/failover/provider_failover.py` | Circuit breakers, failover chains, TPM tracking |
| `app/pipeline/context_compressor.py` | Context window limits per provider |
| `app/agents/contracts.py` | `TokenUsage`, `AgentStatus`, `RetryPolicy` |
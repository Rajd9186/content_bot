# Phase 4: Agent Runtime System

The Agent Runtime System provides a standardized execution framework for all AI agents in the platform. This system handles deterministic execution, typed contracts, retry logic, structured prompting, provider abstraction, validation, observability, and failure recovery.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│              (Phase 3 - Workflow Engine)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Runtime Adapter                     │
│              (app/agents/adapter.py)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Execution Pipeline                        │
│              (app/agents/pipeline.py)                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Input Validation    │ 6. Schema Validation               │
│ 2. Prompt Construction │ 7. Retry Handling                  │
│ 3. Provider Selection  │ 8. Fallback Handling               │
│ 4. LLM Execution       │ 9. Telemetry Capture               │
│ 5. Output Parsing      │ 10. Event Emission                 │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Agents     │  │   Provider   │  │  Validation  │
│ (app/agents/ │  │  Abstraction │  │   & Parsing  │
│  agents/)    │  │  Layer       │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PromptEngine │  │    Models    │  │   Fallback   │
│   & Builder  │  │   & Config   │  │   Recovery   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Key Components

### 1. Base Agent Framework (`app/agents/base.py`)

Provides the abstract `BaseAgent` class with:
- Async execution support
- Cancellation handling
- Timeout management
- Retry integration
- Telemetry collection
- Fallback generation

### 2. Agent Contracts (`app/agents/contracts.py`)

Defines typed interfaces:
- `AgentContract`: Configuration and capabilities
- `AgentInput`/`AgentOutput`: Standardized data structures
- `RetryPolicy`/`TimeoutPolicy`: Execution policies
- `TokenUsage`/`AgentTelemetry`: Observability data

### 3. Execution Pipeline (`app/agents/pipeline.py`)

10-stage deterministic execution flow:
1. Input validation
2. Prompt construction
3. Provider selection
4. LLM execution
5. Output parsing
6. Schema validation
7. Retry handling
8. Fallback handling
9. Telemetry capture
10. Event emission

### 4. Provider Abstraction (`app/agents/provider/`)

Unified interface for:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude series)
- Groq (Llama series)
- Local models (Ollama, llama.cpp)

Features:
- Request/response normalization
- Token tracking
- Rate limit handling
- Automatic retries

### 5. Prompt Engine (`app/agents/prompt/`)

Structured prompt generation:
- System prompts with behavioral constraints
- Developer instructions for output format
- User prompts with contextual information
- Contextual builders for complex scenarios

### 6. Validation & Recovery (`app/agents/validation/`)

Critical fixes implemented:
- **Structured JSON parsing** with recovery from malformed responses
- **Markdown validation** that prevents placeholder content
- **Schema enforcement** at runtime
- **Citation validation** to prevent hallucinations
- **Fallback generation** that preserves original context (not malformed LLM outputs)

### 7. Agent Registry (`app/agents/registry.py`)

Centralized agent management:
- Dynamic registration
- Version tracking
- Capability discovery
- Health monitoring
- Dependency resolution

### 8. Telemetry System (`app/agents/telemetry/`)

Comprehensive observability:
- Token usage tracking
- Execution latency monitoring
- Retry counting
- Error classification
- Workflow correlation

### 9. Retry Framework (`app/agents/retry/`)

Robust error handling:
- Exponential backoff with jitter
- Provider failover
- Error classification
- State preservation

## Critical Fixes Implemented

### 1. Research Summary Quality
**Before**: One-line summaries like "AI is important"
**After**: Substantive analysis with 3+ sentences, specific data points, and contextual relevance

### 2. Prompt Construction
**Before**: Raw key:value dumping
**After**: Structured narrative prompts with clear instructions, context explanation, and formatting rules

### 3. Fallback Generation (MOST CRITICAL)
**Before**: Fallback used malformed LLM response fields, producing "# Untitled" and empty content
**After**: Fallback ALWAYS uses ORIGINAL runtime kwargs, preserving:
- Original title
- Original outline  
- Original research context
- Workflow metadata

This eliminates:
- "# Untitled" outputs
- Empty markdown content
- Fake successful drafts
- Placeholder text persistence

## Agent Types

The system includes 9 specialized agents in `app/agents/agents/`:

1. **Planner** (`planner.py`): Content strategy and structure
2. **Researcher** (`researcher.py`): Information gathering and analysis  
3. **Synthesizer** (`synthesizer.py`): Pattern identification and insight extraction
4. **Outliner** (`outliner.py`): Structured content organization
5. **Writer** (`writer.py`): Content generation and narrative construction
6. **Validator** (`validator.py`): Quality assurance and completeness checking
7. **SEO** (`seo.py`): Search optimization and metadata generation  
8. **FactChecker** (`fact_checker.py`): Verification and citation validation
9. **Finalizer** (`finalizer.py`): Polishing and publication preparation

## Getting Started

### 1. Environment Setup

```bash
# Set API keys for providers you'll use
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  
export GROQ_API_KEY="your-key"

# Optional: Local model endpoint
export LOCAL_MODEL_URL="http://localhost:8000/v1"
```

### 2. Agent Registration

Agents are automatically registered at import time. To manually register:

```python
from app.agents.registry import agent_registry
from app.agents.agents.writer import WriterAgent

# Register agent
agent_registry.register(WriterAgent)

# List all agents
print(agent_registry.list_agents())
```

### 3. Executing Agents

```python
from app.agents.adapter import orchestration_adapter

# Execute through orchestration adapter
result = await orchestration_adapter.execute_agent(
    agent_name="writer",
    correlation_id="workflow-123",
    workflow_id="content-456",
    template_kwargs={
        "title": "AI Ethics Guide",
        "outline": "1. Introduction\n2. Key Principles\n3. Applications",
        "research_synthesis": "AI ethics covers fairness, transparency, and accountability"
    },
    provider_name="openai",  # or "anthropic", "groq", "local"
    model="gpt-4"            # specific model name
)
```

### 4. Monitoring & Observability

```python
from app.agents.telemetry.collector import telemetry_collector

# Get execution summary
summary = telemetry_collector.summary(correlation_id="workflow-123")
print(f"Total tokens: {summary['total_tokens']}")
print(f"Total latency: {summary['total_latency_ms']}ms")
```

## Testing

The test suite (`tests/agents/`) includes comprehensive coverage:

- Unit tests for all components
- Integration tests for agent execution
- Malformed response handling tests
- Provider failure simulation
- Retry logic verification
- Fallback preservation tests
- Schema validation tests

Run tests with:
```bash
cd backend
pytest tests/agents/ -v
```

## Production Considerations

1. **Provider Reliability**: Configure appropriate retry policies in `AgentContract`
2. **Rate Limits**: Monitor token usage through telemetry
3. **Error Handling**: All errors are classified and retried appropriately
4. **Observability**: All executions are traced with correlation IDs
5. **Security**: API keys are loaded from environment variables only
6. **Scalability**: Pipeline caching reduces overhead for repeated executions

## Troubleshooting

### Common Issues

1. **"No valid JSON found"**: LLM produced unparseable output → fallback activated
2. **"Provider execution failed"**: API connectivity issues → automatic retry with backoff  
3. **"Output validation failed"**: Schema mismatch → validation error with details
4. **Timeout errors**: Increase timeout in `TimeoutPolicy`

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check telemetry for execution details:
```python
records = telemetry_collector.get_records(correlation_id="your-id")
for record in records:
    print(f"{record.agent_name}: {record.status} ({record.latency_ms}ms)")
```

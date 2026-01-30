# AGENTS.md - AI Module

## Purpose

Abstraction layer for AI model integrations. Converts natural language to Blender Python code.

## Provider Architecture

```text
┌─────────────────────┐
│   AIProvider (ABC)  │  ← Abstract base class
└─────────┬───────────┘
          │
    ┌─────┴─────┬─────────────┐
    ▼           ▼             ▼
┌────────┐ ┌────────┐ ┌────────────┐
│Anthropic│ │ OpenAI │ │LocalProvider│
│Provider │ │Provider│ │ (Ollama)   │
└────────┘ └────────┘ └────────────┘
```

## Files

| File                    | Purpose                      | Max Lines |
| ----------------------- | ---------------------------- | --------- |
| `provider.py`           | Abstract base class          | 150       |
| `anthropic_provider.py` | Claude integration           | 200       |
| `openai_provider.py`    | GPT integration              | 200       |
| `local_provider.py`     | Ollama/local models          | 200       |
| `prompts/system.py`     | System prompts               | 300       |
| `prompts/templates.py`  | Prompt templates             | 200       |

## Provider Interface

```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def generate_code(
        self,
        user_request: str,
        context: dict | None = None
    ) -> str:
        """Generate Blender Python code from natural language."""
        pass

    @abstractmethod
    async def fix_code(
        self,
        code: str,
        error: str,
        original_request: str
    ) -> str:
        """Fix code that failed execution."""
        pass
```

## System Prompt Requirements

The system prompt must include:

1. Blender Python API basics
2. Common `bpy` operations
3. Safety constraints (logging for filesystem ops)
4. Output format requirements (pure executable Python)

## API Key Management

- Never hardcode API keys
- Use environment variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- Validate keys on provider initialization
- Graceful error if key missing

## Local Model Support

For Ollama integration:

- Default endpoint: `http://localhost:11434`
- Configurable via environment: `OLLAMA_HOST`
- Model selection via config: `OLLAMA_MODEL`

## Error Handling

```python
class AIProviderError(AetherError):
    """Base for AI provider errors."""
    pass

class APIKeyMissingError(AIProviderError):
    """API key not configured."""
    pass

class RateLimitError(AIProviderError):
    """API rate limit exceeded."""
    pass

class ModelUnavailableError(AIProviderError):
    """Requested model not available."""
    pass
```

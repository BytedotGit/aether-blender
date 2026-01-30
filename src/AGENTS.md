# AGENTS.md - Source Code Root

## Purpose

This directory contains all production source code for Aether-Blender.

## Architecture Overview

```text
src/
├── ai/              # AI provider integrations (Claude, GPT, Local)
├── blender_addon/   # Blender-side Python addon
├── bridge/          # External ↔ Blender communication
├── executor/        # Safe code execution and retry logic
├── export/          # Video/file export utilities
├── gui/             # Desktop GUI application (PyQt6)
├── orchestrator/    # Process management and lifecycle
├── project/         # Save/load project functionality
└── telemetry/       # Logging and monitoring
```

## Dependency Rules

```text
gui → orchestrator → bridge → (blender_addon)
                  ↘ ai
                  ↘ executor
                  ↘ project
                  ↘ export
All modules → telemetry
```

## Import Standards

```python
# Absolute imports only
from src.bridge.client import BlenderClient
from src.telemetry.logger import get_logger

# Never relative imports across module boundaries
# Relative imports OK within same module
from .protocol import MessageSchema
```

## Module Creation Checklist

When creating a new module:

1. Create the directory
2. Create `__init__.py` with public exports
3. Create `AGENTS.md` with module-specific instructions
4. Add type stubs if complex
5. Create corresponding test directory in `tests/unit/`

## Shared Exceptions

All custom exceptions inherit from `AetherError`:

```python
# src/exceptions.py
class AetherError(Exception):
    """Base exception for all Aether errors."""
    pass
```

## Type Hints

All functions must have type hints:

```python
def process_request(request: str, timeout: float = 5.0) -> dict[str, Any]:
    """Process a user request and return results."""
    pass
```

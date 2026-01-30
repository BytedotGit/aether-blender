# AGENTS.md - Source Code Root

## Purpose

This directory contains all production source code for Aether-Blender.

---

## MANDATORY REQUIREMENTS

### Every Source File MUST Have:

1. **Corresponding Tests** - `src/module/file.py` → `tests/unit/test_module_file.py`
2. **Logging Integration** - Import and use `get_logger(__name__)`
3. **Type Hints** - All function parameters and return types
4. **Docstrings** - All public functions (Google style)
5. **Input Validation** - Validate at function boundaries

### Before Creating ANY New Code:

1. Read the root `AGENTS.md`
2. Read `docs/NEW_FEATURE_CHECKLIST.md`
3. Plan your tests FIRST
4. Plan your logging points
5. Then implement

---

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

---

## Code Template

Every new Python file should start with this template:

```python
"""
Module description - what this file does.

Part of the <subsystem> component of Aether-Blender.
"""

from src.telemetry.logger import get_logger

logger = get_logger(__name__)


def example_function(param: str, count: int = 0) -> bool:
    """
    Brief description of what this function does.

    Args:
        param: Description of param
        count: Description of count

    Returns:
        Description of return value

    Raises:
        ValueError: When param is invalid
    """
    logger.debug("Entering example_function", extra={"param": param, "count": count})

    # Input validation
    if not isinstance(param, str):
        raise TypeError(f"param must be str, got {type(param).__name__}")
    if not param:
        raise ValueError("param cannot be empty")

    try:
        # Core logic here
        result = True

        logger.debug("Exiting example_function", extra={"result": result})
        return result

    except Exception as e:
        logger.error(
            "Error in example_function",
            extra={"param": param, "error": str(e)}
        )
        raise
```

---

## Module Creation Checklist

When creating a new module:

1. Create the directory
2. Create `__init__.py` with public exports
3. Create `AGENTS.md` with module-specific instructions
4. Add type stubs if complex
5. Create corresponding test directory in `tests/unit/`
6. **Create at least one test file immediately**
7. **Verify logging works before adding logic**

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

---

## Validation Commands

Before committing any source file:

```bash
# Check this specific file
poetry run ruff check src/your_file.py
poetry run black --check src/your_file.py

# Verify tests exist and pass
poetry run pytest tests/unit/test_your_file.py -v

# Full validation
poetry run python scripts/validate_feature.py src/your_file.py
```

---

## Recent Changes

| Date       | Change                          | Tests | Logging | Author |
| ---------- | ------------------------------- | ----- | ------- | ------ |
| 2026-01-30 | Initial telemetry/logger.py     | Yes   | Yes     | Agent  |

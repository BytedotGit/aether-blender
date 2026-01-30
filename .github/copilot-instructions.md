# GitHub Copilot Instructions for Aether-Blender

## Identity

You are an expert Systems Engineer and Python Developer working on **Aether-Blender**, a natural language interface for Blender 3D animation.

## Primary Directives

### 1. Context Loading (MANDATORY)

Before making ANY code changes:

1. Read `AGENTS.md` in the project root
2. Read `AGENTS.md` in the current working directory
3. Check `.aether_state.json` for project state
4. Check `ROADMAP.md` for current phase requirements

### 2. Code Quality Standards

- Maximum 800 lines per file (refactor at 700)
- Use `black` formatting (line length 88)
- Use `ruff` for linting
- Type hints required on all functions
- Google-style docstrings required
- Log entry/exit of every function

### 3. The Closed Loop

Every change must be verified:

- Write code → Run tests → Check logs → Confirm success
- Never assume a change works without verification
- If tests fail, fix before proceeding
- **CI must be green before and after every commit**

### 3.1 CI Pipeline Requirements (MANDATORY)

Before starting ANY work:

1. **Check CI Status:** Verify GitHub Actions is green
2. **Fix Red CI First:** If CI is failing, fixing it is top priority

Before ANY commit:

1. **Run local CI checks:**
   - `poetry run black --check src tests scripts`
   - `poetry run ruff check src tests scripts`
   - `poetry run pytest tests/unit -v`
2. **Fix all VS Code/Pylance errors** - Zero tolerance for type errors
3. **Use `# type: ignore` ONLY for `bpy` module** - Document why with comment

### 4. Commit Protocol

Format: `type(scope): description`
Types: feat, fix, docs, style, refactor, test, chore
Example: `feat(bridge): implement socket handshake`

### 5. Error Philosophy

- Never silently catch exceptions
- Always log errors with context
- Use custom exception hierarchy
- Propagate errors to appropriate handlers

### 6. Testing Requirements

- Every function needs tests
- Name: `test_<function>_<scenario>_<expected>`
- Minimum 80% coverage
- Critical paths: 95% coverage

### 7. Logging Standard

```python
from src.telemetry.logger import get_logger
logger = get_logger(__name__)

def example(param: str) -> bool:
    logger.debug("Entering example", extra={"param": param})
    # ... logic ...
    logger.debug("Exiting example", extra={"result": result})
    return result
```

### 8. Forbidden Actions

- Never use `import *`
- Never use `print()` (use logger)
- Never hardcode paths (use `pathlib.Path`)
- Never commit failing tests
- Never commit with red CI
- Never commit with Pylance/VS Code errors
- Never exceed 800 lines per file
- Never skip type hints

### 9. When Uncertain

Ask the human for clarification rather than guessing. Specifically ask when:

- Multiple valid design approaches exist
- External credentials are needed
- Requirements are ambiguous
- A decision affects architecture

### 10. State Updates

After completing significant work, update `.aether_state.json`:

```json
{
  "last_action": "Description of what you did",
  "last_updated": "ISO timestamp",
  "completed_tasks": ["list", "of", "completed", "items"]
}
```

## Blender-Specific Rules

### Thread Safety

Blender's `bpy` module is NOT thread-safe. All `bpy` operations must:

1. Be queued from background threads
2. Execute on Blender's main thread via `bpy.app.timers`

### Code Execution

Raw Python code sent to Blender must:

1. Be wrapped in try/except
2. Capture stdout/stderr
3. Return structured results
4. Log all filesystem operations

### Connection Management

Always handle:

- Connection refused (Blender not running)
- Connection timeout (Blender frozen)
- Unexpected disconnect (Blender crashed)

## Project-Specific Context

### Current Phase

Check `.aether_state.json` for the active phase.

### Target Environment

- OS: Windows
- Python: 3.11
- Blender: 4.2 LTS (portable installation)
- Package Manager: Poetry

### Repository

- Owner: BytedotGit
- URL: https://github.com/BytedotGit/aether-blender
- Branch Protection: Enabled (require PR, require CI pass)

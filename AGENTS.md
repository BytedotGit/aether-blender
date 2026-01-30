# AGENTS.md - Root Operations Manual

## Purpose

This file is the **primary instruction set** for any AI agent working on the Aether-Blender project. You MUST read this file before making any changes to the codebase.

---

## 1. Project Identity

- **Name:** Aether-Blender
- **Package:** aether-blender
- **Repository:** https://github.com/BytedotGit/aether-blender
- **Python Version:** 3.11
- **Blender Version:** 4.2 LTS

---

## 2. Context Loading Protocol

**CRITICAL:** Before modifying ANY file, you must:

1. Read this root `AGENTS.md` file
2. Read the `AGENTS.md` file in the target directory (if it exists)
3. Check `.aether_state.json` for current project state
4. Check `ROADMAP.md` for phase requirements
5. Check `.github/copilot-instructions.md` for behavioral rules

**If any of these files are missing, CREATE THEM before proceeding.**

---

## 3. Code Quality Laws

### 3.1 The "800 Rule"

- **Maximum lines per file:** 800
- **Warning threshold:** 700 lines
- **Action at threshold:** Refactor into sub-modules immediately
- **Validation:** Pre-commit hook will reject files exceeding 800 lines

### 3.2 Formatting Standards

- **Formatter:** `black` (line length 88)
- **Linter:** `ruff`
- **Type Hints:** Required for all function signatures
- **Docstrings:** Required for all public functions (Google style)

### 3.3 File Naming

- **Python files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/Variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`

---

## 4. Commit Protocol

### 4.1 Message Format

```text
type(scope): short description

[optional body]

[optional footer]
```

### 4.2 Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 4.3 Examples

```text
feat(bridge): implement socket client connection
fix(executor): handle timeout in code execution
docs(readme): add installation instructions
```

---

## 5. Testing Requirements

### 5.1 MANDATORY: Every Feature Gets Tests

**This is non-negotiable.** When you create ANY new:
- Function
- Class
- Module
- API endpoint
- Protocol handler
- GUI component

You MUST create corresponding tests BEFORE considering the feature complete.

### 5.2 Test Creation Checklist

For every new piece of code, create tests that cover:

```text
□ Happy path - Normal expected usage
□ Edge cases - Boundary conditions, empty inputs, max values
□ Error cases - Invalid inputs, missing dependencies, network failures
□ Integration - How it works with other components
□ Regression - Prevents previously fixed bugs from returning
```

### 5.3 Test Coverage

- All new functions must have corresponding tests
- Minimum coverage target: 80%
- Critical paths (bridge, executor): 95% coverage
- **Pre-commit validation:** Files without tests will be flagged

### 5.4 Test Naming

```python
def test_<function_name>_<scenario>_<expected_result>():
    """Test that <function> does <thing> when <condition>."""
    pass
```

### 5.5 Test Location

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- End-to-end tests: `tests/e2e/`

### 5.6 Test File Mapping

Every source file MUST have a corresponding test file:

```text
src/bridge/client.py     → tests/unit/test_bridge_client.py
src/ai/provider.py       → tests/unit/test_ai_provider.py
src/gui/chat_window.py   → tests/unit/test_gui_chat_window.py
```

---

## 6. Debugging & Observability Requirements

### 6.1 MANDATORY: Every Function Gets Debugging

**This is non-negotiable.** Every function, method, and class MUST include:

1. **Entry logging** - Log when entering with input parameters
2. **Exit logging** - Log when exiting with return value
3. **Error logging** - Log all exceptions with full context
4. **State logging** - Log significant state changes

### 6.2 Standard Debugging Pattern

```python
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

def my_function(param: str, count: int) -> bool:
    """Function description."""
    logger.debug(
        "Entering my_function",
        extra={"param": param, "count": count}
    )

    try:
        # Pre-condition validation
        if not param:
            logger.warning("Empty param received", extra={"count": count})
            return False

        # Core logic with state logging
        result = process_data(param)
        logger.debug("Processing complete", extra={"result_size": len(result)})

        # Success path
        logger.debug(
            "Exiting my_function successfully",
            extra={"result": True}
        )
        return True

    except ValueError as e:
        logger.error(
            "Validation error in my_function",
            extra={"param": param, "error": str(e), "error_type": "ValueError"}
        )
        raise
    except Exception as e:
        logger.critical(
            "Unexpected error in my_function",
            extra={"param": param, "error": str(e), "error_type": type(e).__name__}
        )
        raise
```

### 6.3 Log Levels - Precise Definitions

| Level | When to Use | Examples |
|-------|-------------|----------|
| `DEBUG` | Function entry/exit, variable values, loop iterations | "Entering function", "Loop iteration 5" |
| `INFO` | Significant operations, milestones | "Connection established", "File saved" |
| `WARNING` | Recoverable issues, deprecations | "Retry attempted", "Using fallback" |
| `ERROR` | Failures requiring attention | "Connection failed", "Invalid response" |
| `CRITICAL` | System-breaking failures | "Database unreachable", "Config missing" |

### 6.4 Context Data Requirements

Always include relevant context in `extra` dict:

```python
# WRONG - No context
logger.error("Operation failed")

# CORRECT - Full context for debugging
logger.error(
    "Operation failed",
    extra={
        "operation": "send_message",
        "target": "blender",
        "message_id": msg_id,
        "attempt": retry_count,
        "error": str(e)
    }
)
```

### 6.5 Performance Tracking

For operations that may be slow:

```python
import time

def expensive_operation(data):
    start_time = time.perf_counter()
    logger.debug("Starting expensive_operation", extra={"data_size": len(data)})

    result = do_work(data)

    elapsed = time.perf_counter() - start_time
    logger.info(
        "Completed expensive_operation",
        extra={"elapsed_seconds": elapsed, "data_size": len(data)}
    )
    return result
```

---

## 7. Validation Requirements

### 7.1 MANDATORY: Every Feature Gets Validation

When adding ANY new feature, you MUST also:

1. **Update test suite** - Add tests (see Section 5)
2. **Add debugging** - Add logging (see Section 6)
3. **Add input validation** - Validate all inputs at boundaries
4. **Add health checks** - Create ways to verify the feature works
5. **Update documentation** - Document the feature in AGENTS.md

### 7.2 Input Validation Pattern

```python
from typing import Optional
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

def create_object(name: str, size: int, color: Optional[str] = None) -> dict:
    """Create an object with validation."""
    logger.debug("Validating inputs", extra={"name": name, "size": size})

    # Type validation
    if not isinstance(name, str):
        raise TypeError(f"name must be str, got {type(name).__name__}")
    if not isinstance(size, int):
        raise TypeError(f"size must be int, got {type(size).__name__}")

    # Value validation
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if size > 10000:
        raise ValueError(f"size exceeds maximum (10000), got {size}")

    logger.debug("Input validation passed")
    # ... rest of function
```

### 7.3 Health Check Pattern

Every module should expose a health check:

```python
def health_check() -> dict:
    """Return health status of this module."""
    return {
        "module": __name__,
        "status": "healthy",
        "checks": {
            "logger": logger is not None,
            "dependencies": check_dependencies(),
            "config": config_valid(),
        }
    }
```

---

## 8. The Closed Feedback Loop

### 8.1 The Development Cycle

Every new feature MUST follow this cycle:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    CLOSED FEEDBACK LOOP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. PLAN                                                       │
│      └─► Define feature requirements                            │
│      └─► Identify test cases FIRST                              │
│      └─► Document in relevant AGENTS.md                         │
│                     ↓                                           │
│   2. IMPLEMENT                                                  │
│      └─► Write code WITH debugging built-in                     │
│      └─► Add entry/exit logging to EVERY function               │
│      └─► Add input validation                                   │
│                     ↓                                           │
│   3. TEST                                                       │
│      └─► Write unit tests for all code paths                    │
│      └─► Write integration tests if applicable                  │
│      └─► Ensure 80%+ coverage                                   │
│                     ↓                                           │
│   4. VALIDATE                                                   │
│      └─► Run full test suite                                    │
│      └─► Run linting (ruff, black)                              │
│      └─► Verify logging outputs correctly                       │
│      └─► Run validation scripts                                 │
│                     ↓                                           │
│   5. DOCUMENT                                                   │
│      └─► Update AGENTS.md in relevant directory                 │
│      └─► Update .aether_state.json                              │
│      └─► Commit with proper message format                      │
│                     ↓                                           │
│   6. MONITOR (Loop Back)                                        │
│      └─► Check logs for issues                                  │
│      └─► Review test results                                    │
│      └─► Feed learnings back into PLAN                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Pre-Commit Validation Checklist

Before ANY commit, verify:

```text
□ All new functions have corresponding tests
□ All new functions have entry/exit logging
□ All new functions have input validation
□ All tests pass (poetry run pytest)
□ Linting passes (poetry run ruff check src tests scripts)
□ Formatting correct (poetry run black --check src tests scripts)
□ Type checking passes (no Pylance/VS Code errors)
□ No file exceeds 800 lines
□ Relevant AGENTS.md updated
□ .aether_state.json updated
□ CI pipeline is green (check GitHub Actions before starting new work)
```

### 8.3 CI Pipeline Validation

**MANDATORY:** Before starting ANY work, verify CI is green:

1. **Check CI Status First:**
   ```bash
   # Check GitHub Actions status (requires gh CLI)
   gh run list --limit 5
   ```

2. **Run Full Local CI Before Commits:**
   ```bash
   # Run the complete CI validation locally
   poetry run black --check src tests scripts
   poetry run ruff check src tests scripts
   poetry run pytest tests/unit -v
   ```

3. **Fix CI Failures Immediately:**
   - If CI is red, fixing it takes priority over new work
   - Never commit on top of a failing CI
   - All merges require green CI status

4. **Type Checking Requirements:**
   - All VS Code/Pylance errors must be resolved before commit
   - Use `# type: ignore` comments ONLY for Blender-specific code (bpy module)
   - Document why type: ignore is needed with a comment

5. **CI Pipeline Stages:**
   - `code-quality`: black --check, ruff check
   - `unit-tests`: pytest tests/unit
   - `blender-tests`: pytest tests/integration (runs in Blender environment)

### 8.4 New Feature Validation Script

Use `scripts/validate_feature.py` to verify compliance:

```bash
poetry run python scripts/validate_feature.py src/new_module.py
```

The script checks:
- Test file exists for the source file
- Logging is imported and used
- Type hints present on all functions
- Docstrings present on all public functions
- Input validation exists

---

## 9. Error Handling

### 9.1 Exception Hierarchy

```python
class AetherError(Exception):
    """Base exception for all Aether errors."""
    pass

class ConnectionError(AetherError):
    """Blender connection failed."""
    pass

class ExecutionError(AetherError):
    """Code execution in Blender failed."""
    pass
```

### 9.2 Never Silently Fail

```python
# WRONG
try:
    risky_operation()
except:
    pass

# CORRECT
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

---

## 10. Directory Structure

```text
/aether-blender
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   ├── copilot-instructions.md
│   └── PULL_REQUEST_TEMPLATE.md
├── .vscode/
│   ├── settings.json
│   └── extensions.json
├── assets/
│   ├── textures/
│   ├── models/
│   └── projects/
├── docs/
│   └── architecture/
├── logs/
│   └── .gitkeep
├── scripts/
│   ├── setup_blender.py
│   └── AGENTS.md
├── src/
│   ├── ai/
│   │   └── AGENTS.md
│   ├── blender_addon/
│   │   └── AGENTS.md
│   ├── bridge/
│   │   └── AGENTS.md
│   ├── executor/
│   │   └── AGENTS.md
│   ├── export/
│   │   └── AGENTS.md
│   ├── gui/
│   │   └── AGENTS.md
│   ├── orchestrator/
│   │   └── AGENTS.md
│   ├── project/
│   │   └── AGENTS.md
│   ├── telemetry/
│   │   └── AGENTS.md
│   └── AGENTS.md
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── AGENTS.md
├── tools/
│   └── blender/           # Blender installation (git-ignored)
├── .aether_state.json
├── .gitignore
├── .pre-commit-config.yaml
├── AGENTS.md              # THIS FILE
├── LICENSE
├── pyproject.toml
├── README.md
└── ROADMAP.md
```

---

## 11. State Management

### 11.1 State File Location

`.aether_state.json` in project root

### 11.2 State Schema

```json
{
  "current_phase": 1,
  "phase_status": "in_progress",
  "last_action": "Created directory structure",
  "last_updated": "2026-01-30T14:30:00Z",
  "completed_tasks": [],
  "pending_tasks": [],
  "known_issues": [],
  "ci_status": "not_configured"
}
```

### 11.3 Update Protocol

After completing any significant action, update the state file:

```python
# Pseudo-code for agent behavior
state = load_state()
state["last_action"] = "Implemented socket client"
state["last_updated"] = now()
state["completed_tasks"].append("bridge/client.py")
save_state(state)
```

---

## 12. Forbidden Patterns

### 12.1 Never Do These

- Import `*` from any module
- Use global mutable state
- Commit with failing tests
- Skip type hints
- Use `print()` instead of logger
- Hardcode file paths (use `pathlib.Path`)
- Ignore exceptions silently
- Create features without tests
- Create functions without logging
- Skip input validation

### 12.2 Always Do These

- Use `pathlib.Path` for all file operations
- Use context managers (`with` statements) for files/connections
- Validate inputs at function boundaries
- Document complex logic with comments
- Update `AGENTS.md` when adding new modules
- Create tests for EVERY new function
- Add logging to EVERY function
- Run validation before committing

---

## 13. Recovery Instructions

If you (the agent) have lost context:

1. **Read:** `ROADMAP.md` → Understand the big picture
2. **Read:** `.aether_state.json` → Know where we are
3. **Read:** This file → Know the rules
4. **Read:** Target directory `AGENTS.md` → Know local context
5. **Check:** `git log --oneline -10` → See recent changes
6. **Check:** `logs/aether.log` → See recent errors
7. **Run:** `poetry run pytest` → Verify system health

---

## 14. Human Escalation Points

Pause and ask the human when:

- A design decision has multiple valid approaches
- A task requires external credentials (API keys)
- CI is failing and the cause is unclear
- The current phase requirements are ambiguous
- You need to create/modify branch protection rules

---

## Changelog

| Date       | Change                                          | Author        |
| ---------- | ----------------------------------------------- | ------------- |
| 2026-01-30 | Initial creation                                | Human + Agent |
| 2026-01-30 | Added mandatory testing, debugging, validation | Human + Agent |

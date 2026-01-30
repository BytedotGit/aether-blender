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

### 5.1 Test Coverage

- All new functions must have corresponding tests
- Minimum coverage target: 80%
- Critical paths (bridge, executor): 95% coverage

### 5.2 Test Naming

```python
def test_<function_name>_<scenario>_<expected_result>():
    """Test that <function> does <thing> when <condition>."""
    pass
```

### 5.3 Test Location

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- End-to-end tests: `tests/e2e/`

---

## 6. Logging Requirements

### 6.1 Every Function Must Log

```python
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

def my_function(param: str) -> bool:
    logger.debug(f"Entering my_function", extra={"param": param})
    try:
        # ... logic ...
        logger.debug(f"Exiting my_function", extra={"result": result})
        return result
    except Exception as e:
        logger.error(f"Error in my_function", extra={"error": str(e)})
        raise
```

### 6.2 Log Levels

- `DEBUG`: Function entry/exit, variable values
- `INFO`: Significant operations (connection established, file saved)
- `WARNING`: Recoverable issues (retry attempted, fallback used)
- `ERROR`: Failures requiring attention
- `CRITICAL`: System-breaking failures

### 6.3 Log Format

```text
[2026-01-30 14:30:00] [src.bridge.client] [INFO] Message {"context": "data"}
```

---

## 7. Error Handling

### 7.1 Exception Hierarchy

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

### 7.2 Never Silently Fail

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

## 8. Directory Structure

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

## 9. State Management

### 9.1 State File Location

`.aether_state.json` in project root

### 9.2 State Schema

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

### 9.3 Update Protocol

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

## 10. Forbidden Patterns

### 10.1 Never Do These

- Import `*` from any module
- Use global mutable state
- Commit with failing tests
- Skip type hints
- Use `print()` instead of logger
- Hardcode file paths (use `pathlib.Path`)
- Ignore exceptions silently

### 10.2 Always Do These

- Use `pathlib.Path` for all file operations
- Use context managers (`with` statements) for files/connections
- Validate inputs at function boundaries
- Document complex logic with comments
- Update `AGENTS.md` when adding new modules

---

## 11. Recovery Instructions

If you (the agent) have lost context:

1. **Read:** `ROADMAP.md` → Understand the big picture
2. **Read:** `.aether_state.json` → Know where we are
3. **Read:** This file → Know the rules
4. **Read:** Target directory `AGENTS.md` → Know local context
5. **Check:** `git log --oneline -10` → See recent changes
6. **Check:** `logs/aether.log` → See recent errors
7. **Run:** `poetry run pytest` → Verify system health

---

## 12. Human Escalation Points

Pause and ask the human when:

- A design decision has multiple valid approaches
- A task requires external credentials (API keys)
- CI is failing and the cause is unclear
- The current phase requirements are ambiguous
- You need to create/modify branch protection rules

---

## Changelog

| Date       | Change           | Author        |
| ---------- | ---------------- | ------------- |
| 2026-01-30 | Initial creation | Human + Agent |

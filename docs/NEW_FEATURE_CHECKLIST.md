# New Feature Checklist

## Purpose

This checklist MUST be completed for EVERY new feature, module, function, or code addition in the Aether-Blender project. No feature is considered complete until all items are checked.

---

## Pre-Implementation

### Planning
- [ ] Feature requirements documented
- [ ] Test cases identified BEFORE implementation
- [ ] Relevant AGENTS.md files reviewed
- [ ] Dependencies identified

### Design
- [ ] Function signatures defined with type hints
- [ ] Error cases identified
- [ ] Logging points planned
- [ ] Edge cases considered

---

## Implementation

### Code Quality
- [ ] All functions have type hints
- [ ] All public functions have docstrings (Google style)
- [ ] File does not exceed 800 lines
- [ ] No hardcoded paths (using `pathlib.Path`)
- [ ] No `import *` statements
- [ ] No `print()` statements (using logger)

### Debugging & Observability
- [ ] Logger imported: `from src.telemetry.logger import get_logger`
- [ ] Logger instantiated: `logger = get_logger(__name__)`
- [ ] Entry logging for each function
- [ ] Exit logging for each function
- [ ] Error logging with full context
- [ ] Performance logging for slow operations (if applicable)

### Input Validation
- [ ] Type validation for all parameters
- [ ] Value validation (bounds checking, empty strings, etc.)
- [ ] Meaningful error messages on validation failure
- [ ] Validation logged at DEBUG level

### Error Handling
- [ ] Specific exceptions caught (not bare `except:`)
- [ ] Exceptions logged with context before re-raising
- [ ] Custom exceptions used where appropriate
- [ ] No silently swallowed exceptions

---

## Testing

### Unit Tests
- [ ] Test file created: `tests/unit/test_<module>.py`
- [ ] Happy path tests
- [ ] Edge case tests
- [ ] Error case tests
- [ ] All new functions have at least one test
- [ ] Tests follow naming convention: `test_<function>_<scenario>_<expected>`

### Integration Tests (if applicable)
- [ ] Test file created: `tests/integration/test_<feature>.py`
- [ ] Tests interactions between components
- [ ] Tests realistic usage scenarios

### Coverage
- [ ] Coverage meets minimum (80% general, 95% critical paths)
- [ ] All branches covered
- [ ] All error paths tested

---

## Validation

### Automated Checks
- [ ] All tests pass: `poetry run pytest`
- [ ] Linting passes: `poetry run ruff check`
- [ ] Formatting correct: `poetry run black --check`
- [ ] Type checking passes: `poetry run mypy` (if configured)
- [ ] Pre-commit hooks pass

### Manual Verification
- [ ] Feature works as expected in normal usage
- [ ] Error handling behaves correctly
- [ ] Logs are informative and not excessive
- [ ] No regressions in existing functionality

---

## Documentation

### Code Documentation
- [ ] Inline comments for complex logic
- [ ] Type hints complete and accurate
- [ ] Docstrings explain purpose and usage

### Project Documentation
- [ ] Relevant AGENTS.md updated
- [ ] README.md updated (if user-facing feature)
- [ ] .aether_state.json updated
- [ ] ROADMAP.md updated (if milestone completed)

---

## Commit

### Pre-Commit Checklist
- [ ] All items above are checked
- [ ] Changes staged: `git add`
- [ ] Commit message follows format: `type(scope): description`
- [ ] Pre-commit hooks pass

### Commit Message Template
```
feat(scope): brief description of feature

- Added X functionality
- Created tests in tests/unit/test_X.py
- Added logging throughout
- Updated AGENTS.md

Closes #issue_number (if applicable)
```

---

## Quick Validation Command

Run this before committing:

```bash
# Full validation suite
poetry run pytest && \
poetry run ruff check src tests scripts && \
poetry run black --check src tests scripts && \
python scripts/validate_feature.py <your_file.py>
```

---

## Signature

When completing a feature, add an entry to the relevant AGENTS.md:

```markdown
## Recent Changes

| Date       | Feature            | Tests Added | Logging | Author |
| ---------- | ------------------ | ----------- | ------- | ------ |
| YYYY-MM-DD | feature_name       | Yes         | Yes     | Agent  |
```

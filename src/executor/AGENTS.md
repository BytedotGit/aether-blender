# AGENTS.md - Executor Module

## Purpose

Handles safe execution of AI-generated code in Blender, including sandboxing, error capture, retry logic, and execution history.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    ExecutionPipeline                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Validator │→│ Executor │→│ Verifier │→│ Logger │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│        │                           │                    │
│        ▼                           ▼                    │
│  ┌──────────┐              ┌──────────────┐            │
│  │  Reject  │              │ RetryManager │            │
│  └──────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## Files

| File           | Purpose                            | Max Lines |
| -------------- | ---------------------------------- | --------- |
| `pipeline.py`  | Main execution pipeline            | 300       |
| `validator.py` | Pre-execution code validation      | 250       |
| `safe_exec.py` | Sandboxed execution wrapper        | 200       |
| `retry.py`     | Retry logic with exponential backoff| 200       |
| `history.py`   | Execution history tracking         | 200       |
| `verifier.py`  | Post-execution result verification | 200       |

## Pre-Execution Validation

```python
class CodeValidator:
    """Validate code before execution."""
    
    SYNTAX_CHECK = True
    
    # Note: Full trust mode - logging only, not blocking
    LOGGED_PATTERNS = [
        r"import\s+os",
        r"import\s+subprocess",
        r"open\s*\(",
        r"__import__",
        r"eval\s*\(",
        r"exec\s*\(",  # nested exec
    ]
    
    def validate(self, code: str) -> ValidationResult:
        """
        Validate code for execution.
        
        Returns:
            ValidationResult with:
            - is_valid: bool
            - syntax_errors: list[str]
            - warnings: list[str] (logged patterns found)
        """
        pass
```

## Execution Context

```python
# Safe globals provided to exec()
SAFE_GLOBALS = {
    # Blender
    "bpy": bpy,
    "mathutils": mathutils,
    "bmesh": bmesh,
    
    # Python stdlib (safe subset)
    "math": math,
    "random": random,
    "json": json,
    "datetime": datetime,
    
    # Utilities
    "Vector": mathutils.Vector,
    "Matrix": mathutils.Matrix,
    "Euler": mathutils.Euler,
    "Color": mathutils.Color,
}
```

## Retry Strategy

```python
class RetryManager:
    """Handle execution retry with AI-assisted fixes."""
    
    MAX_RETRIES = 3
    
    async def execute_with_retry(
        self,
        code: str,
        original_request: str,
        ai_provider: AIProvider
    ) -> ExecutionResult:
        """
        Execute code with automatic retry on failure.
        
        Flow:
        1. Execute code
        2. If success, return result
        3. If error, ask AI to fix
        4. Execute fixed code
        5. Repeat up to MAX_RETRIES
        6. If all retries fail, return final error
        """
        for attempt in range(self.MAX_RETRIES):
            result = await self.execute(code)
            
            if result.success:
                return result
            
            if attempt < self.MAX_RETRIES - 1:
                code = await ai_provider.fix_code(
                    code=code,
                    error=result.error,
                    original_request=original_request
                )
                logger.info(f"Retry {attempt + 1}: AI suggested fix")
        
        return result  # Final failure
```

## Execution History

```python
@dataclass
class ExecutionRecord:
    id: str
    timestamp: datetime
    request: str           # Original user request
    generated_code: str    # AI-generated code
    result: ExecutionResult
    retries: int
    duration_ms: float
    
class ExecutionHistory:
    """Track all executions for debugging."""
    
    def record(self, record: ExecutionRecord):
        """Save execution to history."""
        pass
    
    def get_recent(self, n: int = 10) -> list[ExecutionRecord]:
        """Get N most recent executions."""
        pass
    
    def get_failures(self) -> list[ExecutionRecord]:
        """Get all failed executions."""
        pass
    
    def export(self, path: Path):
        """Export history for debugging."""
        pass
```

## Result Verification

```python
class ResultVerifier:
    """Verify execution produced expected results."""
    
    async def verify(
        self,
        request: str,
        result: ExecutionResult
    ) -> VerificationResult:
        """
        Verify the result matches the request.
        
        Examples:
        - "create cube" → verify object named "Cube" exists
        - "delete all" → verify scene is empty
        - "move to (1,2,3)" → verify object location
        
        Returns:
            VerificationResult with confidence score
        """
        pass
```

## Error Classification

```python
class ErrorClassifier:
    """Classify errors for appropriate handling."""
    
    def classify(self, error: str) -> ErrorType:
        """
        Classify error type.
        
        SYNTAX_ERROR: Code has syntax issues (AI can fix)
        RUNTIME_ERROR: Code failed during execution (AI might fix)
        BLENDER_ERROR: Blender-specific issue (context, mode)
        RESOURCE_ERROR: Missing file, memory, etc.
        UNKNOWN: Unclassified
        """
        pass
```

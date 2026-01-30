"""
AI Module - System Prompts.

Core system prompts for Blender Python code generation.
These prompts define the AI's behavior and output format.
"""

from typing import Any

from src.telemetry.logger import get_logger

logger = get_logger(__name__)

# System prompt for Blender code generation
BLENDER_SYSTEM_PROMPT = """You are a Blender Python expert assistant. Your task is to generate \
executable Python code that runs inside Blender to accomplish the user's request.

## Core Rules

1. **Output ONLY executable Python code** - No explanations, no markdown, no comments unless \
necessary for the code logic.

2. **Use the `bpy` module** - All Blender operations use `import bpy`.

3. **Assume Blender context** - The code runs inside Blender with full access to bpy.context, \
bpy.data, and bpy.ops.

4. **Handle existing objects** - Check if objects exist before creating duplicates. Use \
`bpy.data.objects.get("name")` to check.

5. **Use proper operators** - Prefer `bpy.ops` for standard operations, but use direct data \
manipulation when more efficient.

6. **Safe file operations** - If writing files, always use absolute paths and log the operation.

## Common Patterns

### Creating primitives:
```python
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "MyCube"
```

### Selecting and modifying:
```python
import bpy
obj = bpy.data.objects.get("Cube")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    obj.location = (1, 2, 3)
```

### Creating materials:
```python
import bpy
mat = bpy.data.materials.new(name="MyMaterial")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 0, 0, 1)
obj.data.materials.append(mat)
```

### Animation keyframes:
```python
import bpy
obj = bpy.context.active_object
obj.location = (0, 0, 0)
obj.keyframe_insert(data_path="location", frame=1)
obj.location = (5, 0, 0)
obj.keyframe_insert(data_path="location", frame=60)
```

## Output Format

Return ONLY the Python code, ready to execute. Example:

```python
import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.active_object
cube.name = "MainCube"
```

Do NOT include:
- Markdown code fences (```)
- Explanatory text before or after the code
- Comments that are not part of the code logic
"""

# Prompt for fixing code that failed execution
CODE_FIX_PROMPT = """You are fixing Blender Python code that failed to execute.

## Original Request
{original_request}

## Code That Failed
```python
{failed_code}
```

## Error Message
```
{error_message}
```

## Your Task
1. Analyze the error message
2. Identify the root cause
3. Generate FIXED Python code that accomplishes the original request

## Common Fixes
- **NameError**: Import missing modules or define variables
- **AttributeError**: Check if object/attribute exists first
- **TypeError**: Verify argument types and counts
- **RuntimeError**: Ensure proper Blender context (edit mode vs object mode)
- **KeyError**: Use `.get()` with default values

## Output
Return ONLY the fixed Python code, ready to execute. No explanations.
"""


def get_generation_prompt(
    user_request: str,
    context: dict[str, Any] | None = None,
) -> str:
    """
    Build the full prompt for code generation.

    Args:
        user_request: The user's natural language request.
        context: Optional context (scene info, history, etc.)

    Returns:
        The complete prompt string.
    """
    logger.debug(
        "Building generation prompt",
        extra={"request_length": len(user_request), "has_context": context is not None},
    )
    from src.ai.prompts.templates import format_context

    prompt_parts = [f"## User Request\n{user_request}"]

    if context:
        context_str = format_context(context)
        if context_str:
            prompt_parts.insert(0, context_str)

    result = "\n\n".join(prompt_parts)
    logger.debug("Generation prompt built", extra={"prompt_length": len(result)})
    return result


def get_fix_prompt(
    code: str,
    error: str,
    original_request: str,
) -> str:
    """
    Build the prompt for fixing failed code.

    Args:
        code: The code that failed.
        error: The error message.
        original_request: The original user request.

    Returns:
        The complete fix prompt string.
    """
    logger.debug(
        "Building fix prompt",
        extra={"code_length": len(code), "error_length": len(error)},
    )
    return CODE_FIX_PROMPT.format(
        original_request=original_request,
        failed_code=code,
        error_message=error,
    )

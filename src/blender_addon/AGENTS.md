# AGENTS.md - Blender Addon Module

## Purpose

Blender-side addon that runs inside Blender's Python environment. Listens for socket connections and executes code on the main thread.

## CRITICAL: Thread Safety

Blender's `bpy` module is **NOT THREAD-SAFE**. You cannot call `bpy` functions from a background thread.

### Solution Architecture

```text
┌─────────────────────┐
│   Socket Thread     │  ← Listens for connections (background)
│   (daemon thread)   │
└─────────┬───────────┘
          │ queue.put(message)
          ▼
┌─────────────────────┐
│   Message Queue     │  ← Thread-safe queue
└─────────┬───────────┘
          │ queue.get()
          ▼
┌─────────────────────┐
│   Timer Callback    │  ← Runs on main thread via bpy.app.timers
│   (main thread)     │
└─────────────────────┘
```

## Files

| File              | Purpose                                   | Max Lines |
| ----------------- | ----------------------------------------- | --------- |
| `__init__.py`     | Addon registration (bl_info, register)    | 150       |
| `server.py`       | Threaded socket server                    | 300       |
| `executor.py`     | Safe code execution with stdout capture   | 250       |
| `queue_handler.py`| Main thread queue processor               | 200       |

## Addon Registration Template

```python
bl_info = {
    "name": "Aether Bridge",
    "author": "Aether Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Aether",
    "description": "Socket bridge for Aether-Blender",
    "category": "Development",
}

def register():
    # Start socket server
    # Register timer
    pass

def unregister():
    # Stop socket server
    # Unregister timer
    # Clean up resources
    pass
```

## Safe Execution Pattern

```python
import sys
from io import StringIO

def execute_safely(code: str) -> dict:
    """Execute code and capture output."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = captured_out = StringIO()
    sys.stderr = captured_err = StringIO()
    
    try:
        exec(code, {"bpy": bpy, "math": math, "mathutils": mathutils})
        return {
            "status": "success",
            "stdout": captured_out.getvalue(),
            "stderr": captured_err.getvalue()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
```

## Memory Leak Prevention

- Always unregister handlers in `unregister()`
- Always stop threads in `unregister()`
- Never store references to Blender objects between executions
- Clear the message queue on unregister

## Testing Notes

This module runs INSIDE Blender. Tests must:

1. Launch Blender with the addon enabled
2. Send commands via socket
3. Verify results via socket response
4. Cannot use pytest directly inside Blender

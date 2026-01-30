# AGENTS.md - Orchestrator Module

## Purpose

Central coordination layer that manages the lifecycle of all system components: Blender process, socket connections, AI providers, and GUI state.

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ BlenderMgr  │  │ BridgeMgr   │  │ AIProviderMgr       │ │
│  │             │  │             │  │                     │ │
│  │ - launch()  │  │ - connect() │  │ - get_provider()    │ │
│  │ - kill()    │  │ - reconnect │  │ - switch_provider() │ │
│  │ - restart() │  │ - health()  │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                           │                                  │
│                    ┌──────▼──────┐                          │
│                    │ StateManager│                          │
│                    │             │                          │
│                    │ - save()    │                          │
│                    │ - restore() │                          │
│                    └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Files

| File                | Purpose                          | Max Lines |
| ------------------- | -------------------------------- | --------- |
| `orchestrator.py`   | Main coordinator class           | 400       |
| `blender_manager.py`| Blender process lifecycle        | 300       |
| `bridge_manager.py` | Connection lifecycle/health      | 250       |
| `ai_manager.py`     | AI provider selection/switching  | 200       |
| `state_manager.py`  | Application state persistence    | 200       |
| `config.py`         | Configuration loading/validation | 150       |

## Blender Manager Responsibilities

### Launch Sequence

```python
class BlenderManager:
    def launch(self, headless: bool = False) -> bool:
        """
        Launch Blender with Aether addon.

        Steps:
        1. Verify Blender executable exists
        2. Verify addon is installed
        3. Launch process with appropriate flags
        4. Wait for socket server to become available
        5. Return success/failure
        """
        pass

    def restart(self) -> bool:
        """
        Restart Blender after crash.

        Steps:
        1. Kill existing process if zombie
        2. Wait for port to be released
        3. Re-launch
        4. Restore last scene state (if available)
        """
        pass
```

### Process Flags

```python
BLENDER_FLAGS = [
    "--python-use-system-env",  # Use system Python packages
    "--enable-autoexec",         # Allow addon auto-execution
]

BLENDER_FLAGS_HEADLESS = [
    "--background",              # No GUI
    "--python-expr", "import bpy; bpy.ops.wm.addon_enable(module='aether_bridge')"
]
```

## Health Monitoring

### Heartbeat Protocol

```python
class BridgeManager:
    async def health_check(self) -> HealthStatus:
        """
        Ping Blender every 5 seconds.

        Returns:
            HealthStatus.HEALTHY - Response received
            HealthStatus.SLOW - Response > 2 seconds
            HealthStatus.UNRESPONSIVE - No response
            HealthStatus.DISCONNECTED - Socket closed
        """
        pass

    async def auto_recover(self, status: HealthStatus):
        """
        Automatic recovery based on health status.

        SLOW: Log warning, continue
        UNRESPONSIVE: Attempt reconnect (3 tries)
        DISCONNECTED: Trigger BlenderManager.restart()
        """
        pass
```

## State Management

### Persisted State

```python
@dataclass
class ApplicationState:
    blender_running: bool
    last_scene_file: Path | None
    ai_provider: str
    chat_history: list[dict]
    window_geometry: dict
    last_successful_command: str | None
```

### Recovery on Crash

When Blender crashes:

1. Save current chat history
2. Note the last command executed
3. Restart Blender
4. Reload last scene (if saved)
5. Notify user via toast
6. Optionally retry last command

## Configuration Schema

```yaml
blender:
  path: "tools/blender/blender.exe"
  startup_timeout: 30
  health_interval: 5

bridge:
  host: "localhost"
  port: 5005
  timeout: 10
  max_retries: 3

ai:
  default_provider: "anthropic"
  anthropic:
    model: "claude-sonnet-4-20250514"
  openai:
    model: "gpt-4"
  local:
    endpoint: "http://localhost:11434"
    model: "codellama"

logging:
  level: "DEBUG"
  file: "logs/aether.log"
```

## Error Escalation

```text
Minor Error (syntax error in generated code)
    → Auto-retry with AI fix (up to 3 times)
    → Show toast notification

Major Error (Blender crash)
    → Auto-restart Blender
    → Show prominent notification
    → Log full traceback

Critical Error (repeated crashes)
    → Stop auto-restart
    → Show error dialog
    → Ask user for guidance
```

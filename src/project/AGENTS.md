# AGENTS.md - Project Module

## Purpose

Handles saving, loading, and managing Aether projects including Blender files, assets, chat history, and configuration.

## Project Structure

```text
my_project/
├── project.aether           # Project metadata (JSON)
├── scene.blend              # Blender scene file
├── assets/
│   ├── textures/
│   ├── models/
│   └── audio/
├── exports/
│   ├── video/
│   └── images/
├── history/
│   └── chat_log.json        # Conversation history
└── backups/
    └── scene_20260130_143000.blend
```

## Files

| File               | Purpose                    | Max Lines |
| ------------------ | -------------------------- | --------- |
| `project.py`       | Project class/operations   | 350       |
| `serializer.py`    | Save/load project metadata | 200       |
| `asset_manager.py` | Asset import/organization  | 300       |
| `backup_manager.py`| Auto-backup functionality  | 200       |
| `history.py`       | Chat history persistence   | 150       |

## Project Metadata Schema

```json
{
  "version": "1.0.0",
  "name": "My Animation",
  "created": "2026-01-30T14:30:00Z",
  "modified": "2026-01-30T15:45:00Z",
  "blender_version": "4.2.0",
  "aether_version": "0.1.0",
  "scene_file": "scene.blend",
  "assets": {
    "textures": ["grass.png", "sky.hdr"],
    "models": ["character.fbx"]
  },
  "settings": {
    "render_engine": "CYCLES",
    "resolution": [1920, 1080],
    "fps": 30
  },
  "ai_context": {
    "style_preferences": "photorealistic, cinematic",
    "scene_description": "A forest clearing at sunset"
  }
}
```

## Auto-Save Protocol

```python
class BackupManager:
    def __init__(self, interval_minutes: int = 5):
        self.interval = interval_minutes
    
    def start_auto_backup(self):
        """
        Every N minutes:
        1. Save current Blender scene to temp
        2. If different from last backup, create new backup
        3. Keep max 10 backups, delete oldest
        4. Log backup creation
        """
        pass
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore from backup:
        1. Confirm with user
        2. Save current state as emergency backup
        3. Load backup file
        4. Update project metadata
        """
        pass
```

## Asset Import Flow

```text
User provides asset (drag-drop, file dialog, URL)
    │
    ▼
Validate asset (format, size, permissions)
    │
    ▼
Copy to project assets/ folder
    │
    ▼
Import into Blender (if applicable)
    │
    ▼
Update project metadata
    │
    ▼
Log and notify user
```

## Chat History Format

```json
{
  "messages": [
    {
      "id": "uuid",
      "timestamp": "2026-01-30T14:30:00Z",
      "role": "user",
      "content": "Create a blue cube"
    },
    {
      "id": "uuid",
      "timestamp": "2026-01-30T14:30:05Z",
      "role": "assistant",
      "content": "I've created a blue cube at the origin.",
      "generated_code": "bpy.ops.mesh.primitive_cube_add()\n...",
      "execution_result": "success"
    }
  ]
}
```

## File Locking

When a project is open:

1. Create `.lock` file in project directory
2. Check for existing lock on open
3. If locked, warn user (may be open elsewhere)
4. Remove lock on clean exit
5. Stale lock detection (> 1 hour old with no process)

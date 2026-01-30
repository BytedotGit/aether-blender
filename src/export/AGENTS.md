# AGENTS.md - Export Module

## Purpose

Handles rendering and exporting animations/scenes to various formats including video (MP4, GIF), images, and 3D formats (BLEND, FBX, GLTF).

## Files

| File               | Purpose                     | Max Lines |
| ------------------ | --------------------------- | --------- |
| `exporter.py`      | Base exporter class/factory | 200       |
| `video_exporter.py`| MP4, GIF, WebM export       | 350       |
| `image_exporter.py`| PNG, JPEG, EXR export       | 250       |
| `model_exporter.py`| FBX, GLTF, OBJ export       | 300       |
| `render_settings.py`| Render config presets      | 200       |
| `progress.py`      | Export progress tracking    | 150       |

## Export Architecture

```text
┌─────────────────┐
│ ExporterFactory │
└────────┬────────┘
         │ creates
    ┌────┴────┬─────────────┐
    ▼         ▼             ▼
┌────────┐ ┌────────┐ ┌──────────┐
│ Video  │ │ Image  │ │  Model   │
│Exporter│ │Exporter│ │ Exporter │
└────────┘ └────────┘ └──────────┘
```

## Video Export Configuration

```python
@dataclass
class VideoExportConfig:
    output_path: Path
    format: Literal["MP4", "GIF", "WEBM"]
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    quality: Literal["low", "medium", "high", "lossless"] = "high"
    start_frame: int = 1
    end_frame: int | None = None  # None = use scene end
    
    # MP4 specific
    codec: str = "H264"
    audio: bool = True
    
    # GIF specific
    loop: bool = True
    optimize: bool = True
```

## Blender Render Commands

```python
def configure_render(config: VideoExportConfig) -> str:
    """Configure Blender render settings."""
    code = f'''
import bpy

scene = bpy.context.scene
scene.render.resolution_x = {config.resolution[0]}
scene.render.resolution_y = {config.resolution[1]}
scene.render.fps = {config.fps}
scene.frame_start = {config.start_frame}
scene.frame_end = {config.end_frame or 'scene.frame_end'}

# Output settings
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = '{config.format}'
scene.render.ffmpeg.codec = '{config.codec}'
scene.render.filepath = r'{config.output_path}'
'''
    return code
```

## Progress Tracking

```python
class ExportProgress:
    """Track and report export progress."""
    
    def __init__(self, total_frames: int):
        self.total = total_frames
        self.current = 0
        self.start_time = None
        self.callbacks: list[Callable] = []
    
    def update(self, frame: int):
        self.current = frame
        progress = (frame / self.total) * 100
        eta = self._calculate_eta()
        for callback in self.callbacks:
            callback(progress, eta)
    
    def on_progress(self, callback: Callable[[float, float], None]):
        """Register progress callback."""
        self.callbacks.append(callback)
```

## Format Support Matrix

| Format | Type  | Use Case                       | Quality  |
| ------ | ----- | ------------------------------ | -------- |
| MP4    | Video | Final delivery, social media   | High     |
| GIF    | Video | Quick previews, web embeds     | Medium   |
| WebM   | Video | Web delivery, transparency     | High     |
| PNG    | Image | Lossless frames, compositing   | Lossless |
| JPEG   | Image | Quick previews                 | Medium   |
| EXR    | Image | HDR, compositing               | Lossless |
| BLEND  | 3D    | Full project, editing          | N/A      |
| FBX    | 3D    | Game engines, other 3D apps    | High     |
| GLTF   | 3D    | Web, AR/VR                     | High     |

## Error Handling

```python
class ExportError(AetherError):
    """Base export error."""
    pass

class RenderFailedError(ExportError):
    """Blender render crashed."""
    pass

class DiskSpaceError(ExportError):
    """Insufficient disk space."""
    pass

class CodecMissingError(ExportError):
    """Required codec not available."""
    pass
```

## Pre-Export Validation

Before starting export:

1. Check disk space (estimate required)
2. Validate output path is writable
3. Verify render settings are valid
4. Check for missing textures/assets
5. Warn if scene is unsaved

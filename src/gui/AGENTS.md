# AGENTS.md - GUI Module

## Purpose

Desktop graphical user interface built with PyQt6. Provides chat interface, visual feedback, and project management for novice users.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                      MainWindow                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   ChatPanel     │  │  PreviewPanel   │  │  AssetBrowser   │ │
│  │                 │  │                 │  │                 │ │
│  │  - MessageList  │  │  - BlenderView  │  │  - TreeView     │ │
│  │  - InputField   │  │  - Controls     │  │  - FileOps      │ │
│  │  - SendButton   │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  [StatusBar] Connection: ✓ | Blender: Running | Phase: Ready   │
├─────────────────────────────────────────────────────────────────┤
│  [ToastManager] - Overlay notifications for feedback            │
└─────────────────────────────────────────────────────────────────┘
```

## Files

| File               | Purpose                            | Max Lines |
| ------------------ | ---------------------------------- | --------- |
| `main_window.py`   | Application main window/layout     | 400       |
| `chat_panel.py`    | Chat interface with history        | 350       |
| `message_widget.py`| Individual message display         | 200       |
| `preview_panel.py` | Blender viewport integration       | 300       |
| `asset_browser.py` | File tree for assets/projects      | 300       |
| `status_bar.py`    | Connection and status display      | 150       |
| `toast_manager.py` | Toast notification system          | 200       |
| `settings_dialog.py`| Configuration dialog              | 350       |
| `styles.py`        | QSS stylesheets and theming        | 200       |
| `signals.py`       | Custom Qt signals                  | 100       |

## Design Principles

### 1. Signal-Slot Architecture

All cross-component communication uses Qt signals:

```python
# In signals.py
from PyQt6.QtCore import pyqtSignal, QObject

class AetherSignals(QObject):
    message_received = pyqtSignal(str, str)  # role, content
    blender_connected = pyqtSignal(bool)
    execution_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    toast_requested = pyqtSignal(str, str)  # message, level
```

### 2. Non-Blocking Operations

All AI and Blender operations must run in QThreads:

```python
from PyQt6.QtCore import QThread, pyqtSignal

class ExecutionWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, code: str):
        super().__init__()
        self.code = code

    def run(self):
        try:
            result = bridge_client.execute(self.code)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### 3. Toast Notification Pattern

```python
class ToastManager:
    def show_success(self, message: str, duration: int = 3000):
        """Green toast, auto-dismiss."""
        pass

    def show_error(self, message: str, duration: int = 5000):
        """Red toast, longer display."""
        pass

    def show_info(self, message: str, duration: int = 3000):
        """Blue toast, informational."""
        pass
```

## Styling Guidelines

- Use QSS for consistent theming
- Dark mode as default (easier on eyes for creative work)
- Accent color: `#4A9EFF` (Aether blue)
- Error color: `#FF4A4A`
- Success color: `#4AFF6E`
- Font: System default, monospace for code

## Accessibility

- All interactive elements must have tooltips
- Keyboard shortcuts for common actions
- Minimum touch target: 44x44 pixels
- High contrast mode support (future)

## Testing Strategy

- Unit tests for signal emissions
- Integration tests for panel interactions
- Manual testing required for visual appearance
- Use `pytest-qt` for Qt-specific testing

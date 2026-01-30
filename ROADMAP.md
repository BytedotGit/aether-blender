# Aether-Blender: Master Roadmap

## Project Vision

Aether-Blender is a natural language interface that allows complete novices to create professional-quality 3D animations in Blender through conversation with AI agents. Users never need to learn Blender's interface or Python scripting.

## Current Status

- **Active Phase:** Phase 2 - The Synapse
- **Last Updated:** 2026-01-30
- **CI Status:** Configured
- **Repository:** https://github.com/BytedotGit/aether-blender

---

## Phase 1: The Iron Foundation (Infrastructure & Environment)

### Objective

Establish a deterministic, reproducible development environment with comprehensive tooling, documentation, and CI/CD pipeline. No feature code—only infrastructure.

### Success Criteria

- [x] Git repository initialized with proper `.gitignore`
- [x] Poetry environment configured with Python 3.11
- [x] Complete directory structure created
- [x] All `AGENTS.md` instruction files in place
- [x] GitHub Copilot instructions configured (`.github/copilot-instructions.md`)
- [x] Pre-commit hooks active (black, ruff, file length check)
- [x] GitHub Actions CI pipeline passing green
- [x] `scripts/setup_blender.py` downloads Blender 4.2 LTS portable
- [x] Blender launch verification test passes
- [x] VS Code workspace configuration complete
- [x] Logging infrastructure skeleton in place
- [x] `.aether_state.json` state tracking file created
- [x] `README.md` with comprehensive setup instructions
- [ ] Branch protection rules configured (requires human intervention)

### Deliverables

| File/Folder                    | Purpose                            |
| ------------------------------ | ---------------------------------- |
| `pyproject.toml`               | Poetry configuration               |
| `.pre-commit-config.yaml`      | Automated code quality enforcement |
| `.github/workflows/ci.yml`     | Continuous integration pipeline    |
| `.github/copilot-instructions.md` | AI agent behavioral rules       |
| `scripts/setup_blender.py`     | Automated Blender installation     |
| `src/telemetry/logger.py`      | Centralized logging system         |
| `tests/test_sanity.py`         | Basic environment verification     |
| `tests/test_blender_launch.py` | Blender executable verification    |

### Estimated Effort

- **Agent Prompts Required:** 8-12
- **Human Intervention Points:** Branch protection setup

---

## Phase 2: The Synapse (Inter-Process Bridge)

### Objective

Establish robust, bi-directional communication between the external Python environment (VS Code/Poetry) and Blender's internal Python environment via TCP sockets.

### Success Criteria

- [x] Blender addon with threaded socket server created
- [x] External Python client library created
- [x] JSON-RPC protocol implemented with schema validation
- [x] Thread-safe execution queue in Blender (main thread execution)
- [x] Connection lifecycle management (connect, disconnect, reconnect)
- [x] Timeout handling and error propagation
- [x] Heartbeat/ping mechanism for connection health
- [x] Integration tests passing (send command, verify execution) - 12/12 tests pass
- [ ] Graceful degradation when Blender is not running

### Technical Architecture

```text
┌─────────────────────┐         TCP Socket        ┌─────────────────────┐
│   External Python   │ ◄─────────────────────►  │   Blender Python    │
│   (Poetry/VS Code)  │        Port 5005         │   (bpy context)     │
├─────────────────────┤                           ├─────────────────────┤
│ BlenderClient       │ ──── JSON-RPC ────────►  │ SocketServer        │
│ - connect()         │                           │ - listen()          │
│ - execute(code)     │                           │ - queue.put()       │
│ - query(data)       │ ◄─── Response ─────────  │ MainThreadExecutor  │
│ - disconnect()      │                           │ - timer callback    │
└─────────────────────┘                           └─────────────────────┘
```

### Deliverables

| File/Folder                       | Purpose                         |
| --------------------------------- | ------------------------------- |
| `src/bridge/client.py`            | External Python socket client   |
| `src/bridge/protocol.py`          | JSON-RPC schema and validation  |
| `src/bridge/exceptions.py`        | Custom exception hierarchy      |
| `src/blender_addon/__init__.py`   | Blender addon registration      |
| `src/blender_addon/server.py`     | Threaded socket server          |
| `src/blender_addon/executor.py`   | Main-thread safe code execution |
| `tests/test_protocol.py`          | Protocol unit tests             |
| `tests/test_connection.py`        | Integration connection tests    |

### Estimated Effort

- **Agent Prompts Required:** 10-15
- **Human Intervention Points:** Manual Blender addon testing

---

## Phase 3: The Cortex (AI Integration & Raw Code Execution)

### Objective

Build the semantic translation layer that converts natural language into executable Blender Python code, with comprehensive error handling and self-correction capabilities.

### Success Criteria

- [ ] AI provider abstraction layer (supports multiple models)
- [ ] OpenAI/Anthropic/Local model integrations
- [ ] Prompt engineering for Blender code generation
- [ ] Safe execution harness with `exec()` wrapper
- [ ] Stdout/stderr capture from Blender execution
- [ ] Error parsing and structured feedback
- [ ] Auto-retry mechanism (up to 3 attempts)
- [ ] Execution history tracking
- [ ] Code validation before execution (syntax check)

### Technical Architecture

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │ ──► │   AI Agent   │ ──► │   Bridge     │ ──► │   Blender    │
│   "make cube"│     │   Claude/GPT │     │   Client     │     │   exec()     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │                                          │
                            │         ┌──────────────┐                 │
                            └──────── │   Feedback   │ ◄───────────────┘
                                      │   Parser     │
                                      └──────────────┘
                                            │
                                      ┌─────▼─────┐
                                      │  Retry?   │
                                      │  Success? │
                                      └───────────┘
```

### Deliverables

| File/Folder                     | Purpose                       |
| ------------------------------- | ----------------------------- |
| `src/ai/provider.py`            | Abstract base class           |
| `src/ai/anthropic_provider.py`  | Claude integration            |
| `src/ai/openai_provider.py`     | GPT integration               |
| `src/ai/local_provider.py`      | Ollama/local model integration|
| `src/ai/prompts/`               | System prompts for generation |
| `src/executor/safe_exec.py`     | Sandboxed execution wrapper   |
| `src/executor/retry.py`         | Auto-retry logic with backoff |
| `src/executor/history.py`       | Execution history tracking    |
| `tests/test_ai_providers.py`    | Provider unit tests           |
| `tests/test_execution.py`       | Execution safety tests        |

### Estimated Effort

- **Agent Prompts Required:** 15-20
- **Human Intervention Points:** API key configuration, model selection

---

## Phase 4: The Interface (GUI & User Experience)

### Objective

Build a polished, novice-friendly GUI using PyQt6 that provides a chat interface, real-time visual feedback, and comprehensive project management.

### Success Criteria

- [ ] Desktop GUI application (PyQt6)
- [ ] Chat interface with message history
- [ ] Toast notifications for success/error feedback
- [ ] Real-time Blender viewport preview (stretch goal)
- [ ] Project save/load functionality
- [ ] Asset browser (textures, models)
- [ ] Export options (MP4, GIF, BLEND, FBX, GLTF)
- [ ] Settings panel (AI provider selection, verbosity, etc.)
- [ ] One-click installer/launcher
- [ ] Auto-restart Blender on crash
- [ ] Comprehensive onboarding for new users

### Technical Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│                        Aether GUI                              │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │   Chat Panel    │  │  Preview Panel  │  │  Asset Panel   │ │
│  │                 │  │                 │  │                │ │
│  │  User: make...  │  │  [Blender View] │  │  📁 Textures   │ │
│  │  AI: Creating.. │  │                 │  │  📁 Models     │ │
│  │                 │  │                 │  │  📁 Projects   │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│  [Status Bar]  Connected ✓  |  Blender: Running  |  GPU: 45%  │
└────────────────────────────────────────────────────────────────┘
```

### Deliverables

| File/Folder                       | Purpose                        |
| --------------------------------- | ------------------------------ |
| `src/gui/main_window.py`          | Main application window        |
| `src/gui/chat_panel.py`           | Chat interface component       |
| `src/gui/preview_panel.py`        | Blender preview component      |
| `src/gui/asset_browser.py`        | Asset management component     |
| `src/gui/settings_dialog.py`      | Configuration interface        |
| `src/gui/notifications.py`        | Toast notification system      |
| `src/orchestrator/launcher.py`    | Application entry point        |
| `src/orchestrator/blender_manager.py` | Blender process lifecycle  |
| `src/project/save_load.py`        | Project serialization          |
| `src/export/video.py`             | MP4/GIF export                 |
| `src/export/formats.py`           | BLEND/FBX/GLTF export          |

### Estimated Effort

- **Agent Prompts Required:** 20-30
- **Human Intervention Points:** UX feedback, design decisions

---

## Phase 5: Production Polish (Future)

### Objective

Final hardening, documentation, and public release preparation.

### Success Criteria

- [ ] Comprehensive user documentation
- [ ] Video tutorials
- [ ] Performance optimization
- [ ] Memory leak testing
- [ ] Cross-platform testing (Windows primary, macOS/Linux stretch)
- [ ] Security audit
- [ ] Public release on GitHub
- [ ] Community feedback integration

---

## Changelog

| Date       | Phase    | Change                    | Author        |
| ---------- | -------- | ------------------------- | ------------- |
| 2026-01-30 | Planning | Initial roadmap created   | Human + Agent |
| 2026-01-30 | Phase 1  | Implementation started    | Agent         |

---

## Context Recovery Instructions

**FOR AGENTS: If you have lost context, follow these steps:**

1. Read this `ROADMAP.md` file completely
2. Check `.aether_state.json` for current phase and last action
3. Read the `AGENTS.md` file in the project root
4. Read the `AGENTS.md` file in the directory you are working in
5. Read `.github/copilot-instructions.md` for behavioral rules
6. Check `logs/` for recent errors or issues
7. Review the most recent commits in git history

**DO NOT PROCEED WITHOUT COMPLETING THESE STEPS.**

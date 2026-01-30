# Aether-Blender

> **Natural language interface for Blender 3D animation. Chat with AI to create professional animations without learning Blender.**

[![CI Pipeline](https://github.com/BytedotGit/aether-blender/actions/workflows/ci.yml/badge.svg)](https://github.com/BytedotGit/aether-blender/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Blender 4.2](https://img.shields.io/badge/blender-4.2%20LTS-orange.svg)](https://www.blender.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Vision

Aether-Blender allows complete novices to create professional-quality 3D animations through natural conversation with AI. No Blender expertise required—just describe what you want to see.

```text
You: "Create a spinning blue cube with dramatic lighting"
Aether: "Done! I've created a blue metallic cube rotating at the origin 
         with a three-point lighting setup. The animation is 120 frames."
```

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Git

### Installation

```powershell
# Clone the repository
git clone https://github.com/BytedotGit/aether-blender.git
cd aether-blender

# Install dependencies
poetry install

# Setup Blender (downloads automatically)
poetry run python scripts/setup_blender.py

# Verify installation
poetry run pytest
```

### First Run

```powershell
# Launch Aether-Blender
poetry run python -m src.orchestrator.launcher
```

## 📁 Project Structure

```text
aether-blender/
├── src/
│   ├── ai/              # AI provider integrations (Claude, GPT, Local)
│   ├── blender_addon/   # Blender-side socket server addon
│   ├── bridge/          # External ↔ Blender communication
│   ├── executor/        # Safe code execution and retry logic
│   ├── export/          # Video/file export utilities
│   ├── gui/             # PyQt6 desktop application
│   ├── orchestrator/    # Process management and lifecycle
│   ├── project/         # Save/load project functionality
│   └── telemetry/       # Logging and monitoring
├── tests/               # Comprehensive test suite
├── scripts/             # Automation scripts
├── assets/              # Textures, models, projects
├── docs/                # Documentation
└── tools/               # Local Blender installation
```

## 🛠️ Development

### Code Quality

This project enforces strict code quality standards:

- **Formatter:** Black (line length 88)
- **Linter:** Ruff
- **Type Hints:** Required for all functions
- **Max File Length:** 800 lines
- **Test Coverage:** 80% minimum

### Running Tests

```powershell
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific module
poetry run pytest tests/unit/bridge/
```

### Pre-commit Hooks

```powershell
# Install hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## 🤖 For AI Agents

This codebase is optimized for autonomous AI development. Before making changes:

1. Read `AGENTS.md` in the project root
2. Read `AGENTS.md` in the target directory
3. Check `.aether_state.json` for current project state
4. Check `ROADMAP.md` for phase requirements

See [AGENTS.md](./AGENTS.md) for complete instructions.

## 📊 Current Status

**Phase 1: The Iron Foundation** (In Progress)

- [x] Project structure
- [x] Documentation framework
- [x] CI/CD pipeline
- [ ] Blender integration tests

See [ROADMAP.md](./ROADMAP.md) for the complete development plan.

## 🔧 Configuration

### Environment Variables

```env
# AI Provider API Keys (set in .env file - not committed)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional: Local model endpoint
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=codellama

# Logging
AETHER_LOG_LEVEL=DEBUG
```

### VS Code

This project includes recommended VS Code settings and extensions. Open the workspace to get prompted to install them.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat(scope): add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All tests pass
- Code follows style guidelines
- Documentation is updated

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Blender Foundation](https://www.blender.org/) for the amazing 3D software
- [Anthropic](https://www.anthropic.com/) and [OpenAI](https://openai.com/) for AI capabilities
- The open-source community

---

**Made with ❤️ by the Aether Team**

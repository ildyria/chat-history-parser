# Quickstart Guide: VS Code Chat History Parser

**Last Updated**: 2026-03-31  
**Target Audience**: Developers new to the project  
**Time to Complete**: 10-15 minutes

---

## Overview

This CLI tool parses VS Code WorkspaceStorage chat session files and outputs structured conversation history in JSON or HTML formats. Built with Python 3.12+, using minimal dependencies and following TDD practices.

---

## Prerequisites

### Required

- **Python 3.12 or higher**
  ```bash
  python3 --version  # Should show 3.12.x or higher
  ```

- **uv** (Python package manager)
  ```bash
  # Install uv if not already installed
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Optional

- **pytest** (for running tests)
- VS Code with chat history data (for testing with real data)

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd chat-history
```

### 2. Set Up Python Environment with uv

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
# Install package in development mode
uv pip install -e .

# Install development dependencies (pytest, etc.)
uv pip install -e ".[dev]"
```

### 4. Verify Installation

```bash
# Check that command is available
chat-history --version
# Expected output: chat-history 1.0.0

# Run test suite
pytest
# Expected: All tests pass
```

---

## Quick Usage

### Find Your WorkspaceStorage Path

```bash
# Linux
ls ~/.config/Code/User/workspaceStorage/

# macOS
ls ~/Library/Application\ Support/Code/User/workspaceStorage/

# Windows
dir %APPDATA%\Code\User\workspaceStorage\
```

Each subdirectory (e.g., `ff0a29140064c53adb63a0d2383e841c`) is a workspace.

### Basic Commands

```bash
# Parse workspace, output JSON to terminal
chat-history ~/.config/Code/User/workspaceStorage/<workspace-id>

# Parse workspace, output HTML to file
chat-history ~/.config/Code/User/workspaceStorage/<workspace-id> -f html

# Save JSON output to file
chat-history ~/.config/Code/User/workspaceStorage/<workspace-id> -o output.json

# Generate HTML with all sessions concatenated chronologically
chat-history ~/.config/Code/User/workspaceStorage/<workspace-id> -f html -c
```

### View Help

```bash
chat-history --help
```

---

## Project Structure

```
chat-history/
├── src/
│   └── chat_history/
│       ├── __init__.py
│       ├── __main__.py       # Entry point (CLI)
│       ├── parser.py          # Core parsing logic
│       ├── models.py          # Data models (WorkspaceContext, ChatSession, Message)
│       ├── html_generator.py  # HTML output generation
│       └── json_serializer.py # JSON output serialization
├── tests/
│   ├── test_parser.py         # Parser unit tests
│   ├── test_cli.py            # CLI integration tests
│   ├── test_html_generator.py # HTML generation tests
│   └── fixtures/              # Sample chatSessions files
├── specs/
│   └── 001-chat-history-parser/
│       ├── spec.md            # Feature specification
│       ├── plan.md            # Implementation plan
│       ├── data-model.md      # Data entities and relationships
│       ├── research.md        # Technology research notes
│       └── contracts/
│           └── cli.md         # CLI interface contract
├── pyproject.toml             # Project metadata and dependencies
├── README.md                  # User-facing documentation
└── .specify/                  # Spec-driven development config
    ├── memory/
    │   └── constitution.md    # Project principles
    └── templates/             # Spec templates
```

---

## Development Workflow

### Test-Driven Development (TDD)

This project follows strict TDD practices:

1. **Write test first**
   ```bash
   # tests/test_parser.py
   def test_parse_user_message():
       session_data = {"requests": [{"message": "Hello", ...}]}
       messages = parse_chat_session(session_data)
       assert len(messages) == 1
       assert messages[0].role == "user"
   ```

2. **Run test (should fail)**
   ```bash
   pytest tests/test_parser.py::test_parse_user_message
   ```

3. **Implement minimum code to pass**
   ```python
   # src/chat_history/parser.py
   def parse_chat_session(session_data):
       requests = session_data.get("requests", [])
       messages = []
       for req in requests:
           msg = req.get("message")
           if msg:
               messages.append(Message(content=msg, role="user", ...))
       return messages
   ```

4. **Run test again (should pass)**
   ```bash
   pytest tests/test_parser.py::test_parse_user_message
   ```

5. **Refactor if needed**, then repeat

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run with coverage report
pytest --cov=chat_history --cov-report=html

# Run tests matching pattern
pytest -k "test_parse"
```

### Code Organization

- **models.py**: Dataclasses for WorkspaceContext, ChatSession, Message
- **parser.py**: Core logic to extract data from chatSessions JSON
- **html_generator.py**: Generate TailwindCSS-styled HTML
- **json_serializer.py**: Serialize data models to JSON
- **__main__.py**: CLI argument parsing and orchestration

---

## Common Tasks

### Add a New CLI Flag

1. Update [`specs/001-chat-history-parser/contracts/cli.md`](specs/001-chat-history-parser/contracts/cli.md) with new flag contract
2. Write test in `tests/test_cli.py`
3. Add argument to argparse in `src/chat_history/__main__.py`
4. Implement feature
5. Update README.md usage examples

### Add Support for New chatSessions Schema Version

1. Add test fixture with new schema version in `tests/fixtures/`
2. Write test in `tests/test_parser.py` for new schema
3. Update `parser.py` to handle new schema fields
4. Update data-model.md if entity structure changes

### Debug Parsing Errors

```bash
# Run with Python stderr output visible
chat-history ~/.config/Code/User/workspaceStorage/<workspace-id> 2>&1

# Test against specific chatSessions file
python3 -c "
import json
from pathlib import Path
from chat_history.parser import parse_chat_session

file = Path('~/.config/Code/User/workspaceStorage/.../chatSessions/abc.json')
data = json.loads(file.expanduser().read_text())
messages = parse_chat_session(data)
print(f'Parsed {len(messages)} messages')
"
```

---

## Architecture Notes

### Design Principles (from Constitution)

1. **Single-Purpose Utility**: Parse chat history only (no modification/creation)
2. **CLI-First Interface**: All functionality via command-line flags
3. **Format Flexibility**: Support JSON and HTML output
4. **Test-Driven Development**: Tests written before implementation
5. **Graceful Error Handling**: Continue on errors, report at end

### Key Technologies

| Technology | Purpose | Source |
|------------|---------|--------|
| Python 3.12+ | Language | Standard |
| argparse | CLI argument parsing | stdlib |
| pathlib | File system operations | stdlib |
| json | JSON parsing | stdlib |
| pytest | Testing framework | PyPI |
| TailwindCSS (CDN) | HTML styling | CDN |
| uv | Package management | Astral |

### Data Flow

```
CLI Input → argparse → models.WorkspaceContext
                             ↓
                    parser.find_chat_sessions()
                             ↓
                    parser.parse_chat_session() → models.Message[]
                             ↓
               json_serializer OR html_generator
                             ↓
                    Output (file or stdout)
```

---

## Troubleshooting

### Command Not Found

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall package
uv pip install -e .
```

### Python Version Error

```bash
# Check Python version
python3 --version

# If < 3.12, install Python 3.12+
# See: https://www.python.org/downloads/
```

### Permission Denied on WorkspaceStorage

```bash
# Check file permissions
ls -la ~/.config/Code/User/workspaceStorage/<workspace-id>

# Ensure read access to chatSessions directory
chmod +r ~/.config/Code/User/workspaceStorage/<workspace-id>/chatSessions/*.json
```

### Empty Output / No Sessions Found

```bash
# Verify chatSessions files exist
find ~/.config/Code/User/workspaceStorage/<workspace-id> -name "*.json"

# Check stderr for warnings
chat-history ~/.config/Code/User/workspaceStorage/<workspace-id> 2>&1 | grep Warning
```

---

## Next Steps

### For Users

1. Read [`README.md`](../../README.md) for detailed usage instructions
2. Check [`contracts/cli.md`](contracts/cli.md) for complete CLI reference
3. Report issues or request features via GitHub Issues

### For Contributors

1. Read [`spec.md`](spec.md) for feature requirements
2. Review [`plan.md`](plan.md) for implementation design
3. Study [`data-model.md`](data-model.md) for entity relationships
4. Follow TDD workflow (write tests first!)
5. Run tests before committing: `pytest`

### For Maintainers

1. Review [`constitution.md`](../../.specify/memory/constitution.md) before major changes
2. Update [`plan.md`](plan.md) when adding features
3. Keep [`contracts/cli.md`](contracts/cli.md) in sync with CLI changes
4. Follow semantic versioning for releases

---

## Resources

- **Spec Documents**: [`specs/001-chat-history-parser/`](../001-chat-history-parser/)
- **Constitution**: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md)
- **CLI Contract**: [`contracts/cli.md`](contracts/cli.md)
- **Python argparse**: https://docs.python.org/3/library/argparse.html
- **TailwindCSS Docs**: https://tailwindcss.com/docs
- **pytest Docs**: https://docs.pytest.org/

---

## Summary

**Time Investment**: 10-15 minutes to set up and run first parse  
**Learning Curve**: Low (standard Python CLI patterns)  
**Next Command**: `chat-history ~/.config/Code/User/workspaceStorage/<workspace-id> -f html`

You're now ready to develop and use the VS Code Chat History Parser! 🚀

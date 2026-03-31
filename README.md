# Chat History Parser

Parse VS Code WorkspaceStorage chat session files into structured JSON and styled HTML formats.

## Overview

This tool extracts conversation history from VS Code's internal chat session storage (`workspaceStorage/<workspace-id>/chatSessions/*.json`) and converts it into readable formats:

- **JSON**: Structured data for programmatic analysis
- **HTML**: Styled output with GitHub Copilot-like chat interface using TailwindCSS

## Features

- 📂 Parse entire WorkspaceStorage directories
- 💬 Extract chat messages with minimal metadata (content, timestamp, role)
- 🎨 Generate HTML with Copilot-style layout (user messages right, assistant left)
- 📊 Export structured JSON for automation
- 🛡️ Graceful error handling for corrupted files
- 🔀 Support multiple workspaces and concatenation modes
- 🚀 Zero runtime dependencies beyond Python 3.12 stdlib

## Installation

### Using uv (recommended)

```bash
# Clone or download the project
cd chat-history-parser

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Generate HTML output (default: single file to stdout)
chat-history-parser ~/.config/Code/User/workspaceStorage/ff0a29140064c53adb63a0d2383e841c

# Save to file
chat-history-parser ~/.config/Code/User/workspaceStorage/ff0a29140064c53adb63a0d2383e841c -o output.html

# Generate JSON instead
chat-history-parser ~/.config/Code/User/workspaceStorage/ff0a29140064c53adb63a0d2383e841c --format json

# Multiple workspaces with concatenation
chat-history-parser ~/.config/Code/User/workspaceStorage/ --concatenate -o merged.html
```

### Common Options

```bash
-f, --format {json|html}    Output format (default: html)
-o, --output PATH           Output file path (default: stdout)
-m, --html-mode MODE        HTML output mode: single|per-session|per-workspace
-c, --concatenate           Merge sessions chronologically
-h, --help                  Show help message
-v, --version               Show version number
```

## Output Formats

### HTML Output

Generates self-contained HTML files with:
- TailwindCSS styling (loaded via CDN)
- Copilot-style chat interface
- User messages: right-aligned, blue background
- Assistant messages: left-aligned, white background
- Actions/tools: left-aligned, gray muted background
- Responsive design with dark mode support

### JSON Output

Structured data with:
- Metadata (generation timestamp, workspace path, counts)
- Array of chat sessions with sessionId and dates
- Array of messages with content, timestamp, and role
- Parse error summary (if any)

## Development

### Running Tests

```bash
# Install development dependencies
uv pip install pytest

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m contract
```

### Project Structure

```
src/chat_history_parser/    # Application code
├── __init__.py             # Package initialization
├── __main__.py             # CLI entry point
├── cli.py                  # Argument parsing
├── parser.py               # chatSessions parsing
├── models.py               # Data classes
├── scanner.py              # Workspace scanning
├── errors.py               # Custom exceptions
└── formatters/             # Output generators
    ├── json_formatter.py   # JSON output
    └── html_formatter.py   # HTML output

tests/                      # Test code
├── unit/                   # Function-level tests
├── integration/            # End-to-end tests
├── contract/               # Schema validation
└── fixtures/               # Sample data files
```

## Requirements

- Python 3.12 or higher
- No runtime dependencies (uses stdlib only)
- Development: pytest for testing

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Troubleshooting

### "FileNotFoundError: WorkspaceStorage path not found"

Ensure the path points to a valid VS Code WorkspaceStorage directory containing `chatSessions/` subdirectories.

### "No chat sessions found"

The workspace may not have any chat history yet. Try with a workspace where you've used GitHub Copilot Chat.

### HTML file won't open

HTML files require TailwindCSS from CDN. Ensure you have internet connectivity when first opening the file.

## Documentation

- [Specification](specs/001-chat-history-parser/spec.md) - Feature requirements
- [Technical Plan](specs/001-chat-history-parser/plan.md) - Architecture and design
- [Data Model](specs/001-chat-history-parser/data-model.md) - Entity definitions
- [CLI Contract](specs/001-chat-history-parser/contracts/cli.md) - Interface guarantees
- [Quickstart Guide](specs/001-chat-history-parser/quickstart.md) - Developer onboarding

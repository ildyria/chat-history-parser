# Research: VS Code Chat History Parser

**Phase**: 0 - Research & Outline  
**Date**: 2026-03-31  
**Purpose**: Resolve technical unknowns and establish best practices for implementation

---

## 1. Python 3.12+ CLI Architecture

### Decision
Use **argparse** with standard patterns:
- `ArgumentParser` with description and epilog
- `add_argument()` for both positional and optional arguments
- Short (`-f`) and long (`--format`) option names
- `choices` parameter for constrained values
- `action='store_true'` for boolean flags
- Custom `type` functions for validation

### Rationale
- Built-in to Python standard library (zero dependencies)
- Well-documented and universally understood
- Native support for GNU-style arguments
- Automatic help generation with `-h/--help`
- Type coercion and validation built-in
- argparse is more feature-rich than alternatives like click (which would add a dependency)

### Alternatives Considered
- **click**: More elegant API but adds external dependency (violates minimal dependency principle)
- **sys.argv parsing**: Too low-level, requires manual help text and validation
- **docopt**: Interesting approach but less mainstream and adds dependency

### Implementation Notes
```python
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(
    prog='chat-history',
    description='Parse VS Code WorkspaceStorage chat sessions',
    epilog='Example: chat-history ~/.config/Code/User/workspaceStorage/abc123 -f html'
)

parser.add_argument(
    'workspace_path',
    type=Path,
    help='Path to VS Code WorkspaceStorage directory'
)

parser.add_argument(
    '-f', '--format',
    choices=['json', 'html'],
    default='json',
    help='Output format (default: json)'
)

parser.add_argument(
    '-o', '--output',
    type=Path,
    help='Output file path (default: stdout for JSON, chat-history.html for HTML)'
)

parser.add_argument(
    '-m', '--html-mode',
    choices=['single', 'per-session', 'per-workspace'],
    default='single',
    help='HTML file structure mode (default: single)'
)

parser.add_argument(
    '-c', '--concatenate',
    action='store_true',
    help='Merge all sessions chronologically'
)

parser.add_argument(
    '-v', '--version',
    action='version',
    version='%(prog)s 0.1.0'
)

args = parser.parse_args()
```

**Exit Codes**:
- `0`: Success
- `1`: Invalid arguments or path not found
- `2`: Parsing errors (partial or complete failures)

---

## 2. File System Traversal with pathlib

### Decision
Use **pathlib.Path** for all file operations with these patterns:
- `Path.exists()` and `Path.is_dir()` for validation
- `Path.glob('**/*.json')` for recursive file discovery
- `Path.read_text()` for reading JSON files
- `Path.write_text()` for writing output files
- Exception handling for permission/locked file errors

### Rationale
- Object-oriented API more readable than `os.path`
- Cross-platform path handling built-in
- Recursive glob patterns with `**` wildcard
- Context-aware exception messages
- Python 3.12+ has excellent pathlib performance

### Alternatives Considered
- **os.walk()**: More verbose, string-based paths less elegant
- **os.path + glob**: Requires mixing multiple modules
- **scandir**: Lower-level, unnecessary complexity

### Implementation Notes
```python
from pathlib import Path
import json

def find_chat_sessions(workspace_path: Path) -> list[Path]:
    """Recursively find all chatSessions JSON files."""
    if not workspace_path.exists():
        raise FileNotFoundError(f"Path does not exist: {workspace_path}")
    
    if not workspace_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {workspace_path}")
    
    # Pattern: workspaceStorage/*/chatSessions/*.json
    pattern = "*/chatSessions/*.json"
    return list(workspace_path.glob(pattern))

def safe_read_json(file_path: Path) -> dict | None:
    """Read JSON file with error handling."""
    try:
        content = file_path.read_text(encoding='utf-8')
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Warning: Malformed JSON in {file_path}: {e}", file=sys.stderr)
        return None
    except PermissionError:
        print(f"Warning: Permission denied: {file_path}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"Warning: Cannot read {file_path}: {e}", file=sys.stderr)
        return None
```

**Glob Pattern**: `*/chatSessions/*.json` matches `<workspace-id>/chatSessions/<session-file>.json`

---

## 3. JSON Parsing & Schema Validation

### Decision
Use **standard library `json` module** with manual schema validation:
- `json.loads()` with try/except for JSONDecodeError
- Defensive dict access with `.get(key, default)`
- Type checking with `isinstance()`
- No external schema validation library (pydantic, jsonschema)

### Rationale
- Minimizes dependencies (aligns with constitution)
- chatSessions schema is undocumented and may vary
- Defensive parsing more resilient than strict schema validation
- Explicit validation logic easier to debug than schema DSL
- Performance: json module is C-optimized

### Alternatives Considered
- **pydantic**: Excellent type validation but adds dependency; overkill for simple parsing
- **jsonschema**: Formal validation but requires maintaining separate schema file
- **marshmallow**: Adds complexity and dependency for marginal benefit

### Implementation Notes
```python
import json
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    content: str
    timestamp: datetime
    role: str  # 'user' or 'assistant'

def parse_chat_session(session_data: dict) -> list[Message]:
    """Extract messages from chatSessions v3 schema."""
    messages = []
    
    # Defensive schema access
    requests = session_data.get('requests', [])
    if not isinstance(requests, list):
        return messages
    
    for request in requests:
        if not isinstance(request, dict):
            continue
        
        # User message
        user_msg = request.get('message')
        timestamp_str = request.get('timestamp')
        if user_msg and timestamp_str:
            messages.append(Message(
                content=str(user_msg),
                timestamp=parse_timestamp(timestamp_str),
                role='user'
            ))
        
        # Assistant responses (array of mixed types)
        responses = request.get('response', [])
        if not isinstance(responses, list):
            continue
        
        for response_item in responses:
            if isinstance(response_item, dict):
                # Text response
                text = response_item.get('value')
                if text:
                    messages.append(Message(
                        content=str(text),
                        timestamp=parse_timestamp(timestamp_str),
                        role='assistant'
                    ))
    
    return messages

def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp."""
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return datetime.now()  # Fallback to current time
```

**Key Pattern**: Use `.get()` with defaults and `isinstance()` checks at every level to handle schema variations gracefully.

---

## 4. Test-Driven Development with pytest

### Decision
Use **pytest** with this structure:
- `tests/` directory mirroring `src/` structure
- Fixtures for sample data and temp directories
- Parametrize tests for multiple input scenarios
- Separate unit tests (functions) and integration tests (CLI)
- `pytest-cov` for coverage reporting

### Rationale
- pytest is the de facto standard for Python testing
- Fixtures provide clean setup/teardown
- Parametrize reduces test duplication
- Excellent assertion introspection
- Easy to run (`pytest` command)
- Coverage integration available

### Alternatives Considered
- **unittest**: Standard library but more verbose and less powerful
- **doctest**: Good for documentation but insufficient for comprehensive testing
- **nose**: Deprecated in favor of pytest

### Implementation Notes
```python
# tests/test_parser.py
import pytest
from pathlib import Path
from chat_history.parser import parse_chat_session, Message

@pytest.fixture
def sample_session():
    """Fixture for valid chatSessions JSON."""
    return {
        "version": 3,
        "sessionId": "abc123",
        "creationDate": "2026-03-31T10:00:00Z",
        "requests": [
            {
                "requestId": "req1",
                "message": "Hello",
                "timestamp": "2026-03-31T10:00:01Z",
                "response": [
                    {"value": "Hi there!"}
                ]
            }
        ]
    }

def test_parse_valid_session(sample_session):
    """Test parsing valid chatSessions file."""
    messages = parse_chat_session(sample_session)
    
    assert len(messages) == 2
    assert messages[0].role == 'user'
    assert messages[0].content == 'Hello'
    assert messages[1].role == 'assistant'
    assert messages[1].content == 'Hi there!'

@pytest.mark.parametrize("invalid_input,expected_count", [
    ({}, 0),  # Empty dict
    ({"requests": None}, 0),  # Invalid requests
    ({"requests": [{}]}, 0),  # Missing fields
    ({"requests": [{"message": "hi"}]}, 1),  # Partial data
])
def test_parse_malformed_data(invalid_input, expected_count):
    """Test graceful handling of malformed data."""
    messages = parse_chat_session(invalid_input)
    assert len(messages) == expected_count

# tests/test_cli.py
import subprocess

def test_cli_version():
    """Test --version flag."""
    result = subprocess.run(
        ['chat-history', '--version'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert 'chat-history' in result.stdout

def test_cli_invalid_path():
    """Test error handling for nonexistent path."""
    result = subprocess.run(
        ['chat-history', '/nonexistent/path'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert 'does not exist' in result.stderr.lower()
```

**TDD Workflow**:
1. Write test for next feature
2. Run test (should fail)
3. Implement minimal code to pass
4. Refactor if needed
5. Repeat

---

## 5. Error Handling & Logging

### Decision
Use **stderr for errors + exit codes**:
- Print descriptive errors to `sys.stderr`
- Use `print(..., file=sys.stderr)` (no logging module)
- Return specific exit codes (0=success, 1=user error, 2=data error)
- Include context in error messages (file paths, line numbers)
- Continue processing on individual file errors (partial success)

### Rationale
- Simple and direct for CLI tools
- No configuration overhead (logging module overkill for simple CLI)
- stderr convention well-understood by Unix tools
- Exit codes enable shell scripting integration
- Partial success aligns with "graceful error handling" principle

### Alternatives Considered
- **logging module**: Too heavyweight for single-purpose CLI; adds configuration complexity
- **Raise exceptions**: Would require top-level try/catch; less user-friendly messages
- **Silent failures**: Violates transparency and debuggability

### Implementation Notes
```python
import sys

def main():
    try:
        args = parse_args()
        
        # Validate inputs
        if not args.workspace_path.exists():
            print(f"Error: Path does not exist: {args.workspace_path}", file=sys.stderr)
            sys.exit(1)
        
        # Find and parse files
        session_files = find_chat_sessions(args.workspace_path)
        
        if not session_files:
            print(f"Warning: No chat session files found in {args.workspace_path}", file=sys.stderr)
            # Exit 0 - not an error, just no data
            sys.exit(0)
        
        parsed_sessions = []
        error_count = 0
        
        for session_file in session_files:
            try:
                data = safe_read_json(session_file)
                if data:
                    messages = parse_chat_session(data)
                    parsed_sessions.append((session_file, messages))
                else:
                    error_count += 1
            except Exception as e:
                print(f"Error parsing {session_file}: {e}", file=sys.stderr)
                error_count += 1
        
        # Generate output
        if args.format == 'json':
            output_json(parsed_sessions, args.output)
        else:
            output_html(parsed_sessions, args.output, args.html_mode)
        
        # Report summary
        print(f"Parsed {len(parsed_sessions)} sessions successfully", file=sys.stderr)
        if error_count > 0:
            print(f"Failed to parse {error_count} sessions", file=sys.stderr)
            sys.exit(2)  # Partial failure
        
        sys.exit(0)  # Success
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard Unix exit code for SIGINT
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Error Message Format**: `{Level}: {Description}: {Context}`
- Example: `Error: Path does not exist: /tmp/invalid`
- Example: `Warning: Malformed JSON in abc123.json: Expecting value at line 45`

---

## 6. HTML Generation with TailwindCSS

### Decision
Use **string templating with f-strings**:
- Build HTML programmatically with Python f-strings
- Include TailwindCSS 3.x via CDN (`<script src="https://cdn.tailwindcss.com"></script>`)
- Embed all content in a single HTML file (no external resources except CDN)
- Use semantic HTML5 elements (`<article>`, `<section>`, `<time>`)

### Rationale
- No template engine dependency needed for simple HTML
- f-strings are readable and fast
- TailwindCSS CDN requires zero build step
- Single file = works offline after generation (CDN cached by browser)
- Semantic HTML improves accessibility

### Alternatives Considered
- **jinja2**: Powerful templating but adds dependency; overkill for simple structure
- **html module**: Too low-level, escaping without structure
- **dominate**: Pythonic HTML generation but adds dependency
- **Standalone Tailwind**: Requires Node.js build process (violates constitution)

### Implementation Notes

**TailwindCSS CDN**: Use Play CDN for development/simple deployment:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat History</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom styles for code blocks and syntax highlighting */
        pre { @apply bg-gray-900 text-gray-100 rounded p-4 overflow-x-auto; }
        code { @apply font-mono text-sm; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-gray-900">
    <!-- Content here -->
</body>
</html>
```

**Chat UI Pattern**:
```python
def generate_message_html(message: Message) -> str:
    """Generate HTML for a single message."""
    role_class = "bg-blue-100 dark:bg-blue-900" if message.role == "user" else "bg-gray-100 dark:bg-gray-800"
    role_label = "You" if message.role == "user" else "Assistant"
    
    return f"""
    <div class="mb-4 p-4 rounded-lg {role_class}">
        <div class="flex items-center justify-between mb-2">
            <span class="font-semibold text-gray-900 dark:text-gray-100">{role_label}</span>
            <time class="text-sm text-gray-600 dark:text-gray-400">{message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</time>
        </div>
        <div class="text-gray-800 dark:text-gray-200 prose dark:prose-invert max-w-none">
            {escape_html(message.content)}
        </div>
    </div>
    """

def generate_html_output(sessions: list[tuple[Path, list[Message]]], mode: str) -> str:
    """Generate complete HTML document."""
    
    if mode == 'single':
        # All sessions in one file with TOC
        toc_items = [f'<li><a href="#session-{i}" class="text-blue-600 hover:underline">Session {i+1}</a></li>' 
                     for i in range(len(sessions))]
        toc_html = f'<nav class="mb-8"><ul class="list-disc pl-6">{"".join(toc_items)}</ul></nav>'
        
        session_htmls = []
        for i, (session_file, messages) in enumerate(sessions):
            messages_html = "".join(generate_message_html(msg) for msg in messages)
            session_htmls.append(f'''
                <section id="session-{i}" class="mb-12">
                    <h2 class="text-2xl font-bold mb-4 text-gray-900 dark:text-gray-100">Session {i+1}</h2>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">Source: {session_file.name}</p>
                    {messages_html}
                </section>
            ''')
        
        content = toc_html + "".join(session_htmls)
    
    else:
        # Per-session or per-workspace modes would generate separate files
        # (Implementation similar but returns list of (filename, html) tuples)
        pass
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VS Code Chat History</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 dark:bg-gray-900 p-8">
    <div class="max-w-4xl mx-auto">
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">VS Code Chat History</h1>
            <p class="text-gray-600 dark:text-gray-400">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        <main>
            {content}
        </main>
    </div>
</body>
</html>
"""

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;'))
```

**Tailwind Classes for Chat UI**:
- Container: `max-w-4xl mx-auto` (centered, readable width)
- User messages: `bg-blue-100 dark:bg-blue-900`
- Assistant messages: `bg-gray-100 dark:bg-gray-800`
- Typography: `prose dark:prose-invert` (Tailwind Typography plugin via CDN)
- Timestamps: `text-sm text-gray-600 dark:text-gray-400`

**Dark Mode Support**: Use `dark:` variants automatically (respects `prefers-color-scheme`)

---

## Summary

All technical unknowns resolved. Ready for Phase 1 design:

| Area | Decision | Dependency | 
|------|----------|------------|
| CLI Framework | argparse | stdlib |
| File System | pathlib | stdlib |
| JSON Parsing | json + defensive validation | stdlib |
| Testing | pytest | external |
| Error Handling | stderr + exit codes | stdlib |
| HTML Generation | f-strings + TailwindCSS CDN | stdlib + CDN |

**Zero additional runtime dependencies** beyond Python 3.12 standard library.  
**Development dependency**: pytest (for testing only).

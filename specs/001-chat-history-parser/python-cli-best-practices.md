# Python 3.12+ CLI Best Practices Guide

**Project**: VS Code Chat History Parser  
**Date**: 2026-03-31  
**Purpose**: Production-ready patterns for single-purpose CLI utilities

---

## 1. argparse Best Practices

### Decision
Use `argparse` with a dedicated parser function that returns a namespace, separating argument definition from business logic. Use subparsers only if multiple commands exist (not needed for single-purpose tools).

### Rationale
- **Standard library**: No external dependencies
- **GNU-style support**: Native `-f`/`--format` patterns
- **Type conversion**: Built-in type validation via `type=` parameter
- **Help generation**: Automatic `--help` based on argument definitions
- **Python 3.12+ enhancements**: Better error messages and validation

### Alternatives Considered
- **Click**: More features but adds dependency; overkill for simple CLI
- **Typer**: Type hints for args but requires external package
- **sys.argv parsing**: Manual parsing is error-prone and lacks help generation
- **getopt**: C-style, less Pythonic than argparse

### Implementation Notes

```python
import argparse
import sys
from pathlib import Path

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="chat-history-parser",
        description="Parse VS Code WorkspaceStorage chat sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserve formatting
        epilog="Examples:\n"
               "  %(prog)s /path/to/WorkspaceStorage\n"
               "  %(prog)s /path/to/WorkspaceStorage -f json -o output.json\n"
               "  %(prog)s /path/to/WorkspaceStorage --concatenate"
    )
    
    # Version flag (action='version' exits automatically)
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    # Required positional argument with type validation
    parser.add_argument(
        "workspace_path",
        type=Path,  # Automatic conversion to Path object
        help="path to VS Code WorkspaceStorage directory"
    )
    
    # Format with choices (validates automatically)
    parser.add_argument(
        "-f", "--format",
        choices=["json", "html"],
        default="html",
        help="output format (default: %(default)s)"
    )
    
    # Output path (optional, defaults to stdout for JSON)
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="output file path (default: stdout for JSON, auto-generated for HTML)"
    )
    
    # HTML-specific options
    parser.add_argument(
        "-m", "--html-mode",
        choices=["single", "per-session", "per-workspace"],
        default="single",
        help="HTML output structure (default: %(default)s)"
    )
    
    # Boolean flag (store_true means default is False)
    parser.add_argument(
        "-c", "--concatenate",
        action="store_true",
        help="merge all sessions by timestamp"
    )
    
    # Verbosity flag (can be repeated: -vv)
    parser.add_argument(
        "--verbose",
        action="count",
        default=0,
        help="increase logging verbosity (can be repeated)"
    )
    
    return parser


def main():
    """Entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validation logic (not in argparse for complex rules)
    if args.format == "json" and args.html_mode != "single":
        parser.error("--html-mode only applies to HTML format")
    
    if not args.workspace_path.exists():
        parser.error(f"path does not exist: {args.workspace_path}")
    
    if not args.workspace_path.is_dir():
        parser.error(f"path is not a directory: {args.workspace_path}")
    
    # Business logic here
    print(f"Parsing: {args.workspace_path}")
    print(f"Format: {args.format}")
    print(f"Concatenate: {args.concatenate}")


if __name__ == "__main__":
    main()
```

**Key Patterns**:
- Use `type=Path` for automatic path conversion
- Use `choices=` for enum-like validation
- Use `default=` and `%(default)s` in help text
- Use `action="store_true"` for boolean flags
- Use `action="count"` for verbosity levels
- Separate parser creation from business logic (testable)
- Perform complex validation after parsing, using `parser.error()` for consistent formatting
- Use `RawDescriptionHelpFormatter` for examples section

**Gotchas**:
- `argparse.FileType` opens files immediately—avoid it, use `Path` and open manually
- `parser.error()` writes to stderr and exits with code 2 (convention for usage errors)
- Use `dest=` to rename argument variables: `--html-mode` → `args.html_mode`

---

## 2. pathlib Patterns

### Decision
Use `pathlib.Path` exclusively for all file system operations. Use `rglob()` for recursive scanning, `match()` for pattern validation, and explicit exception handling for permission errors.

### Rationale
- **Cross-platform**: Automatic path separator handling (`/` vs `\`)
- **Chainable**: `path.parent.parent / "file.txt"` is readable
- **Type-safe**: Path objects prevent string concatenation bugs
- **Rich API**: `exists()`, `is_dir()`, `read_text()`, `glob()` built-in
- **Python 3.12+**: Performance improvements and new methods like `walk()`

### Alternatives Considered
- **os.path**: Legacy, harder to compose paths
- **glob module**: Requires string paths, less intuitive
- **os.walk**: More verbose than `Path.walk()` or `rglob()`

### Implementation Notes

```python
from pathlib import Path
from typing import Iterator
import json
import sys

def find_chat_sessions(workspace_storage: Path) -> Iterator[Path]:
    """
    Locate all chatSessions JSON files in WorkspaceStorage.
    
    Pattern: <workspace-id>/chatSessions/<hex>.json
    where workspace-id is 32-char hex, hex is variable-length hex filename
    """
    # Use rglob for recursive search (Python 3.5+)
    # More efficient than os.walk, handles symlinks safely
    for json_file in workspace_storage.rglob("*.json"):
        # Validate path structure (granular control)
        if json_file.parent.name == "chatSessions":
            workspace_id = json_file.parent.parent.name
            # Validate 32-character hex workspace ID
            if len(workspace_id) == 32 and all(c in "0123456789abcdef" for c in workspace_id):
                yield json_file


def find_chat_sessions_v2(workspace_storage: Path) -> Iterator[Path]:
    """Alternative using glob pattern matching (less validation)."""
    # Match specific pattern with wildcards
    # */chatSessions/*.json matches one level deep per *
    # More efficient but less control over validation
    pattern = "[0-9a-f]" * 32 + "/chatSessions/*.json"
    for json_file in workspace_storage.glob(pattern):
        yield json_file


def safe_read_json(file_path: Path) -> dict | None:
    """
    Read JSON file with comprehensive error handling.
    
    Returns parsed dict on success, None on any error.
    Logs specific error context to stderr.
    """
    try:
        # read_text() is safer than open() for text files
        # Handles encoding automatically (UTF-8 default)
        content = file_path.read_text(encoding="utf-8")
        return json.loads(content)
    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return None
    
    except PermissionError:
        print(f"Error: Permission denied: {file_path}", file=sys.stderr)
        return None
    
    except OSError as e:  # Covers locked files, I/O errors
        print(f"Error: Cannot read file {file_path}: {e}", file=sys.stderr)
        return None
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path} at line {e.lineno}: {e.msg}", 
              file=sys.stderr)
        return None
    
    except UnicodeDecodeError as e:
        print(f"Error: Invalid encoding in {file_path}: {e}", file=sys.stderr)
        return None


def validate_output_path(output_path: Path) -> bool:
    """
    Validate output path is writable before processing.
    
    Fail fast to avoid wasting time parsing if we can't write output.
    """
    try:
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Test writability (create empty file or check existing)
        if output_path.exists():
            if not output_path.is_file():
                print(f"Error: Output path is not a file: {output_path}", 
                      file=sys.stderr)
                return False
            # Check if we can write to existing file
            if not output_path.stat().st_mode & 0o200:  # Owner write bit
                print(f"Error: Output file is not writable: {output_path}", 
                      file=sys.stderr)
                return False
        else:
            # Test by creating and immediately deleting
            output_path.touch()
            output_path.unlink()
        
        return True
    
    except PermissionError:
        print(f"Error: Permission denied: {output_path.parent}", file=sys.stderr)
        return False
    
    except OSError as e:
        print(f"Error: Cannot create output file: {e}", file=sys.stderr)
        return False


def get_relative_path_for_display(base: Path, target: Path) -> str:
    """
    Get relative path for user-friendly display.
    
    Falls back to absolute path if relative calculation fails.
    """
    try:
        return str(target.relative_to(base))
    except ValueError:
        # target is not under base
        return str(target.absolute())


# Python 3.12+ specific: Path.walk() method
def find_chat_sessions_py312(workspace_storage: Path) -> Iterator[Path]:
    """
    Python 3.12+ version using walk() for better control.
    
    walk() yields (dirpath, dirnames, filenames) like os.walk
    but with Path objects.
    """
    for dirpath, dirnames, filenames in workspace_storage.walk():
        if dirpath.name == "chatSessions":
            for filename in filenames:
                if filename.endswith(".json"):
                    yield dirpath / filename
            # Don't descend into subdirectories of chatSessions
            dirnames.clear()
```

**Key Patterns**:
- Use `rglob("*.json")` for recursive directory scanning
- Always use `encoding="utf-8"` explicitly in `read_text()`
- Use `mkdir(parents=True, exist_ok=True)` for safe directory creation
- Test file writeability before processing (fail fast)
- Use `relative_to()` for user-friendly path display
- Handle `PermissionError`, `OSError`, `FileNotFoundError` separately for specific messages
- Use `Path.walk()` in Python 3.12+ for better performance

**Gotchas**:
- `rglob()` follows symlinks by default—can cause infinite loops
- `exists()` returns `False` for broken symlinks (use `is_symlink()` to detect)
- `read_text()` reads entire file into memory—not suitable for huge files
- Path comparison is case-sensitive on Linux, case-insensitive on macOS/Windows
- `Path("/path") / Path("/other")` returns `/other` (absolute path joins replace)

---

## 3. JSON Parsing Resilience

### Decision
Use standard library `json` with schema validation via dataclasses or TypedDict. Implement progressive parsing: extract what's valid, report what's broken, never discard recoverable data.

### Rationale
- **Standard library**: `json` module is fast and sufficient for most cases
- **Validation**: Dataclasses provide structure without external dependencies
- **Error recovery**: Try-except at granular level (per-message vs per-file)
- **Performance**: `json` is C-optimized; avoid `orjson` unless profiling shows need
- **Schema**: TypedDict + type checker for validation without runtime overhead

### Alternatives Considered
- **pydantic**: Powerful but adds dependency; overkill for simple schema
- **jsonschema**: External validation but slower than dataclasses
- **orjson**: Faster but requires C extension, complicates distribution
- **ujson**: Faster but can lose precision on floats; less stable than stdlib

### Implementation Notes

```python
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Iterator
from datetime import datetime

# Schema definition using dataclasses (Python 3.12+: no future import needed)
@dataclass
class ChatMessage:
    """Single message in chat session."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: int  # Unix timestamp in milliseconds
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMessage | None":
        """
        Create ChatMessage from dict with validation.
        
        Returns None if data is invalid, allowing partial extraction.
        """
        try:
            return cls(
                role=str(data["role"]),
                content=str(data.get("content", "")),  # Default empty
                timestamp=int(data["timestamp"])
            )
        except (KeyError, ValueError, TypeError) as e:
            # Log but don't crash—allow partial extraction
            print(f"Warning: Skipping invalid message: {e}", file=sys.stderr)
            return None


@dataclass
class ChatSession:
    """Complete chat session with metadata."""
    workspace_id: str
    session_file: str
    messages: list[ChatMessage]
    created_at: int
    
    @classmethod
    def from_file(cls, file_path: Path) -> "ChatSession | None":
        """
        Parse chat session from JSON file with resilience.
        
        Implements progressive parsing: extract valid messages even if
        some are corrupted. Returns None only if file is completely unreadable.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error: Cannot read {file_path}: {e}", file=sys.stderr)
            return None
        
        # Parse JSON with specific error handling
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            # Try to extract partial JSON if possible
            print(f"Error: Invalid JSON in {file_path} at line {e.lineno}, column {e.colno}: {e.msg}",
                  file=sys.stderr)
            
            # Attempt recovery: parse up to error position
            partial_content = content[:e.pos]
            try:
                # Try to close any open structures
                if partial_content.rstrip().endswith(','):
                    partial_content = partial_content.rstrip()[:-1]
                # Add closing braces/brackets (heuristic)
                data = json.loads(partial_content + ']}')
                print(f"Warning: Recovered partial data from {file_path}", 
                      file=sys.stderr)
            except json.JSONDecodeError:
                # Recovery failed
                return None
        
        # Validate schema and extract messages
        try:
            workspace_id = file_path.parent.parent.name
            session_file = file_path.name
            
            # Handle VS Code chatSessions v3 schema: requests array with nested messages
            requests = data.get("requests", [])
            messages: list[ChatMessage] = []
            
            for request in requests:
                # Extract user message
                if "request" in request:
                    user_msg = ChatMessage.from_dict({
                        "role": "user",
                        "content": request["request"].get("message", ""),
                        "timestamp": request.get("timestamp", 0)
                    })
                    if user_msg:
                        messages.append(user_msg)
                
                # Extract assistant responses (may be multiple)
                if "response" in request and isinstance(request["response"], list):
                    for resp in request["response"]:
                        # Handle various response types
                        content = ""
                        if isinstance(resp, dict):
                            # Text response
                            if "content" in resp:
                                content = resp["content"]
                            # Tool response (extract text only)
                            elif "text" in resp:
                                content = resp["text"]
                        elif isinstance(resp, str):
                            content = resp
                        
                        if content:
                            assistant_msg = ChatMessage.from_dict({
                                "role": "assistant",
                                "content": content,
                                "timestamp": request.get("timestamp", 0)
                            })
                            if assistant_msg:
                                messages.append(assistant_msg)
            
            # Even if no messages, return valid session (empty is valid)
            return cls(
                workspace_id=workspace_id,
                session_file=session_file,
                messages=messages,
                created_at=data.get("createdAt", 0)
            )
        
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error: Invalid schema in {file_path}: {e}", file=sys.stderr)
            return None


def parse_multiple_files(file_paths: list[Path]) -> Iterator[ChatSession]:
    """
    Parse multiple JSON files, yielding valid sessions.
    
    Continues processing even if individual files fail.
    Reports errors but doesn't crash on corrupted data.
    """
    success_count = 0
    error_count = 0
    
    for file_path in file_paths:
        session = ChatSession.from_file(file_path)
        if session:
            success_count += 1
            yield session
        else:
            error_count += 1
    
    # Summary to stderr after processing
    print(f"\nParsed {success_count} sessions successfully, {error_count} failed",
          file=sys.stderr)


# Performance optimization: use json.load with file object for large files
def parse_large_file_streaming(file_path: Path) -> dict | None:
    """
    Parse large JSON file using file object (streaming read).
    
    json.load() reads in chunks, reduces memory usage vs read_text().
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)  # Slightly more efficient than loads(read())
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None


# Alternative: TypedDict for static type checking without runtime overhead
from typing import TypedDict, NotRequired

class MessageDict(TypedDict):
    """Type hint for message structure (static checking only)."""
    role: str
    content: NotRequired[str]  # Optional field (Python 3.11+)
    timestamp: int

# Use with type checker: mypy, pyright
def process_message(msg: MessageDict) -> None:
    print(msg["role"])  # Type checker validates key exists
    print(msg.get("content", ""))  # Type checker knows this is valid
```

**Key Patterns**:
- Use dataclasses with `from_dict()` class methods for validation
- Parse at granular level: per-message, per-session (not all-or-nothing)
- Use `get()` with defaults for optional fields
- Attempt partial recovery from `JSONDecodeError` using error position
- Keep error messages specific (file, line, column, error type)
- Count successes/failures and report summary
- Use `json.load(file_obj)` for files >10MB (streaming)

**Gotchas**:
- `json.loads()` is slightly faster than `json.load()` for small files (<1MB)
- `JSONDecodeError.pos` is byte position, not character position with Unicode
- Partial recovery is heuristic—may produce garbage data, validate afterward
- Don't catch `Exception` broadly—be specific to preserve stack traces
- `orjson` is 2-3x faster but complicates packaging; profile before adding dependency

---

## 4. pytest TDD Approach

### Decision
Structure tests with `conftest.py` for fixtures, use `tmp_path` for file system isolation, parametrize for multiple scenarios, and mock only external dependencies (not internal functions).

### Rationale
- **pytest**: Modern test framework with excellent fixtures and plugins
- **Isolation**: `tmp_path` fixture provides clean filesystem per test
- **Parametrization**: Test multiple inputs without duplication
- **Coverage**: `pytest-cov` integrates seamlessly
- **TDD workflow**: Write test → run (fail) → implement → run (pass)

### Alternatives Considered
- **unittest**: Standard library but more verbose, less flexible
- **nose**: Deprecated, superceded by pytest
- **hypothesis**: Property-based testing is powerful but adds complexity
- **mocking filesystem**: `pyfakefs` is comprehensive but heavyweight

### Implementation Notes

```python
# tests/conftest.py - Shared fixtures
import pytest
from pathlib import Path
import json

@pytest.fixture
def sample_workspace(tmp_path: Path) -> Path:
    """
    Create sample WorkspaceStorage structure for testing.
    
    tmp_path is a pytest built-in fixture providing isolated directory.
    Automatically cleaned up after test.
    """
    workspace_id = "a" * 32  # Valid 32-char hex
    chat_sessions_dir = tmp_path / workspace_id / "chatSessions"
    chat_sessions_dir.mkdir(parents=True)
    
    # Create sample chat session file
    session_file = chat_sessions_dir / "abc123.json"
    session_data = {
        "version": 3,
        "createdAt": 1234567890000,
        "requests": [
            {
                "timestamp": 1234567890000,
                "request": {
                    "message": "Hello, assistant!"
                },
                "response": [
                    {"content": "Hello! How can I help you?"}
                ]
            }
        ]
    }
    session_file.write_text(json.dumps(session_data), encoding="utf-8")
    
    return tmp_path


@pytest.fixture
def corrupted_workspace(tmp_path: Path) -> Path:
    """
    Create WorkspaceStorage with corrupted JSON files.
    
    Used to test error handling and partial recovery.
    """
    workspace_id = "b" * 32
    chat_sessions_dir = tmp_path / workspace_id / "chatSessions"
    chat_sessions_dir.mkdir(parents=True)
    
    # Invalid JSON (truncated)
    (chat_sessions_dir / "bad1.json").write_text('{"version": 3, "requests": [', encoding="utf-8")
    
    # Valid JSON but invalid schema
    (chat_sessions_dir / "bad2.json").write_text('{"invalid": "schema"}', encoding="utf-8")
    
    # Empty file
    (chat_sessions_dir / "empty.json").write_text('', encoding="utf-8")
    
    return tmp_path


# tests/test_parser.py - Test suite
import pytest
from pathlib import Path
from chat_parser import find_chat_sessions, ChatSession, ChatMessage

class TestChatSessionDiscovery:
    """Tests for locating chat session files."""
    
    def test_finds_valid_chat_sessions(self, sample_workspace: Path):
        """Should find all valid chatSessions JSON files."""
        sessions = list(find_chat_sessions(sample_workspace))
        assert len(sessions) == 1
        assert sessions[0].name == "abc123.json"
    
    def test_ignores_invalid_workspace_ids(self, tmp_path: Path):
        """Should skip directories with non-hex workspace IDs."""
        # Create invalid workspace ID (not 32-char hex)
        invalid_dir = tmp_path / "not-a-workspace-id" / "chatSessions"
        invalid_dir.mkdir(parents=True)
        (invalid_dir / "session.json").write_text('{}', encoding="utf-8")
        
        sessions = list(find_chat_sessions(tmp_path))
        assert len(sessions) == 0
    
    def test_empty_directory_returns_no_sessions(self, tmp_path: Path):
        """Should return empty list for directory with no sessions."""
        sessions = list(find_chat_sessions(tmp_path))
        assert len(sessions) == 0


class TestChatSessionParsing:
    """Tests for parsing chat session JSON files."""
    
    def test_parses_valid_session(self, sample_workspace: Path):
        """Should extract messages from valid session file."""
        session_file = list(find_chat_sessions(sample_workspace))[0]
        session = ChatSession.from_file(session_file)
        
        assert session is not None
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Hello, assistant!"
        assert session.messages[1].role == "assistant"
    
    def test_handles_corrupted_json(self, corrupted_workspace: Path):
        """Should return None for corrupted JSON, log error."""
        session_file = corrupted_workspace / ("b" * 32) / "chatSessions" / "bad1.json"
        session = ChatSession.from_file(session_file)
        
        assert session is None
    
    def test_extracts_valid_messages_from_mixed_data(self, tmp_path: Path):
        """Should extract valid messages even if some are corrupted."""
        workspace_id = "c" * 32
        chat_sessions_dir = tmp_path / workspace_id / "chatSessions"
        chat_sessions_dir.mkdir(parents=True)
        
        # Mix of valid and invalid messages
        session_data = {
            "version": 3,
            "createdAt": 1234567890000,
            "requests": [
                {
                    "timestamp": 1111111111111,
                    "request": {"message": "Valid message"},
                    "response": [{"content": "Valid response"}]
                },
                {
                    "timestamp": 2222222222222,
                    # Missing request field
                    "response": [{"content": "Orphan response"}]
                },
                {
                    "timestamp": 3333333333333,
                    "request": {"message": "Another valid"},
                    "response": [{"content": "Another response"}]
                }
            ]
        }
        session_file = chat_sessions_dir / "mixed.json"
        session_file.write_text(json.dumps(session_data), encoding="utf-8")
        
        session = ChatSession.from_file(session_file)
        assert session is not None
        # Should have 4 messages (2 valid user + 2 valid assistant)
        # Orphan response should still be extracted
        assert len(session.messages) >= 3


# Parametrized tests for multiple scenarios
@pytest.mark.parametrize("role,content,timestamp,expected_valid", [
    ("user", "Hello", 1234567890000, True),
    ("assistant", "Hi there", 1234567890000, True),
    ("invalid_role", "Message", 1234567890000, True),  # Should convert to string
    ("user", "", 1234567890000, True),  # Empty content is valid
    ("user", "Message", -1, True),  # Negative timestamp is valid (edge case)
])
def test_message_creation(role: str, content: str, timestamp: int, expected_valid: bool):
    """Test ChatMessage creation with various inputs."""
    msg = ChatMessage.from_dict({
        "role": role,
        "content": content,
        "timestamp": timestamp
    })
    assert (msg is not None) == expected_valid


class TestCLIIntegration:
    """Integration tests for complete CLI workflow."""
    
    def test_end_to_end_json_output(self, sample_workspace: Path, capsys):
        """Should parse workspace and output JSON to stdout."""
        from chat_parser import main
        import sys
        
        # Mock sys.argv for argparse
        sys.argv = ["chat-parser", str(sample_workspace), "-f", "json"]
        
        main()
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        
        assert len(output) == 1
        assert output[0]["workspace_id"] == "a" * 32
    
    def test_handles_nonexistent_path(self, capsys):
        """Should exit with error for nonexistent path."""
        from chat_parser import main
        import sys
        
        sys.argv = ["chat-parser", "/nonexistent/path"]
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "does not exist" in captured.err


# Testing file system errors with monkeypatch
def test_handles_permission_error(sample_workspace: Path, monkeypatch):
    """Should handle PermissionError gracefully."""
    session_file = list(find_chat_sessions(sample_workspace))[0]
    
    # Mock Path.read_text to raise PermissionError
    def mock_read_text(*args, **kwargs):
        raise PermissionError("Access denied")
    
    monkeypatch.setattr(Path, "read_text", mock_read_text)
    
    session = ChatSession.from_file(session_file)
    assert session is None  # Should return None, not crash


# Performance test (not run by default)
@pytest.mark.slow
def test_parses_many_files_quickly(tmp_path: Path):
    """Should parse 100 session files in <5 seconds."""
    import time
    
    # Create 100 session files
    for i in range(100):
        workspace_id = format(i, '032x')
        chat_sessions_dir = tmp_path / workspace_id / "chatSessions"
        chat_sessions_dir.mkdir(parents=True)
        
        session_file = chat_sessions_dir / f"{i:08x}.json"
        session_data = {
            "version": 3,
            "createdAt": 1234567890000,
            "requests": [
                {
                    "timestamp": 1234567890000 + i,
                    "request": {"message": f"Message {i}"},
                    "response": [{"content": f"Response {i}"}]
                }
            ]
        }
        session_file.write_text(json.dumps(session_data), encoding="utf-8")
    
    start = time.time()
    sessions = list(find_chat_sessions(tmp_path))
    for session_file in sessions:
        ChatSession.from_file(session_file)
    elapsed = time.time() - start
    
    assert len(sessions) == 100
    assert elapsed < 5.0  # Performance requirement
```

**Running tests**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chat_parser --cov-report=term-missing

# Run only unit tests (fast)
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::TestChatSessionParsing::test_parses_valid_session

# Run in TDD mode (watch for changes)
pytest-watch
```

**Key Patterns**:
- Use `tmp_path` fixture for isolated filesystem per test
- Create reusable fixtures in `conftest.py` for common test data
- Use `capsys` fixture to capture stdout/stderr
- Use `monkeypatch` to mock file system errors without external libraries
- Parametrize tests to cover multiple scenarios without duplication
- Test both success paths and error paths
- Write integration tests that exercise complete workflows
- Mark slow tests with `@pytest.mark.slow` and skip by default

**Gotchas**:
- `tmp_path` is unique per test—can't share between tests (use `tmp_path_factory` for sharing)
- `capsys.readouterr()` consumes output—call only once per assertion
- `sys.argv` mutation affects other tests—use `monkeypatch.setattr()` instead
- pytest discovers tests by `test_` prefix—functions, classes, files
- Fixtures with `yield` run cleanup after test—use for setup/teardown

---

## 5. Error Handling Patterns

### Decision
Use structured logging (not print) for errors and warnings. Define specific exit codes for different error conditions. Preserve full context in error messages (file path, line number, operation). Use stderr for all errors, stdout only for data.

### Rationale
- **Separation**: stdout for data, stderr for diagnostics (enables `| jq` pipelines)
- **Exit codes**: Communicate error type to shell scripts (0=success, 1=general error, 2=usage error)
- **Context**: Include file path, operation, and error type in every error message
- **Logging**: Structured logs enable filtering, formatting, and analysis
- **User-friendly**: Technical details in error messages but plain language explanations

### Alternatives Considered
- **Rich library**: Beautiful terminal output but adds dependency
- **Click.echo**: Tied to Click framework
- **Print to stderr**: Works but lacks structure, harder to filter
- **Exceptions for control flow**: Anti-pattern, makes debugging harder

### Implementation Notes

```python
import sys
import logging
from pathlib import Path
from enum import IntEnum
from typing import NoReturn

# Define exit codes as constants (POSIX conventions)
class ExitCode(IntEnum):
    """Exit codes for CLI tool."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    USAGE_ERROR = 2  # Invalid arguments
    INPUT_ERROR = 3  # Input file/directory issues
    OUTPUT_ERROR = 4  # Output file write issues
    PARTIAL_SUCCESS = 5  # Some files processed, some failed


# Configure logging at module level
def setup_logging(verbose: int = 0) -> logging.Logger:
    """
    Configure logging with appropriate level.
    
    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
    
    Returns:
        Configured logger instance
    """
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    
    # Create logger
    logger = logging.getLogger("chat_parser")
    logger.setLevel(level)
    
    # Create stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    # Create formatter with context
    formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s",  # Simple format for CLI
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Global logger (initialized in main)
logger = logging.getLogger("chat_parser")


def error_and_exit(message: str, exit_code: ExitCode = ExitCode.GENERAL_ERROR) -> NoReturn:
    """
    Print error message and exit with specified code.
    
    Use for fatal errors where recovery is impossible.
    """
    logger.error(message)
    sys.exit(exit_code)


def warn(message: str) -> None:
    """
    Print warning message to stderr.
    
    Use for non-fatal issues where processing can continue.
    """
    logger.warning(message)


# Context-preserving error messages
def handle_file_read_error(file_path: Path, error: Exception) -> None:
    """
    Log file read error with full context.
    
    Includes: file path, error type, error message, recovery action.
    """
    if isinstance(error, FileNotFoundError):
        logger.error(f"File not found: {file_path}")
    elif isinstance(error, PermissionError):
        logger.error(f"Permission denied: {file_path}")
    elif isinstance(error, OSError):
        logger.error(f"Cannot read file '{file_path}': {error}")
    elif isinstance(error, UnicodeDecodeError):
        logger.error(f"Invalid encoding in '{file_path}': {error.reason}")
    else:
        logger.error(f"Unexpected error reading '{file_path}': {error}")


def handle_json_parse_error(file_path: Path, error: Exception) -> None:
    """
    Log JSON parse error with specific location.
    
    JSONDecodeError includes line/column numbers—include in message.
    """
    if isinstance(error, json.JSONDecodeError):
        logger.error(
            f"Invalid JSON in '{file_path}' "
            f"at line {error.lineno}, column {error.colno}: {error.msg}"
        )
    else:
        logger.error(f"Cannot parse JSON in '{file_path}': {error}")


# Usage example in main function
def main():
    """Entry point with comprehensive error handling."""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_path", type=Path)
    parser.add_argument("-f", "--format", choices=["json", "html"], default="html")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--verbose", action="count", default=0)
    
    args = parser.parse_args()
    
    # Setup logging based on verbosity
    global logger
    logger = setup_logging(args.verbose)
    
    # Validate input path
    if not args.workspace_path.exists():
        error_and_exit(
            f"WorkspaceStorage path does not exist: {args.workspace_path}",
            ExitCode.INPUT_ERROR
        )
    
    if not args.workspace_path.is_dir():
        error_and_exit(
            f"WorkspaceStorage path is not a directory: {args.workspace_path}",
            ExitCode.INPUT_ERROR
        )
    
    # Validate output path if specified
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            error_and_exit(
                f"Cannot create output directory: {e}",
                ExitCode.OUTPUT_ERROR
            )
    
    # Parse sessions with error tracking
    success_count = 0
    error_count = 0
    
    logger.info(f"Scanning {args.workspace_path} for chat sessions...")
    
    session_files = list(find_chat_sessions(args.workspace_path))
    
    if not session_files:
        logger.warning(f"No chat session files found in {args.workspace_path}")
        print("[]" if args.format == "json" else "<html><body>No sessions found</body></html>")
        sys.exit(ExitCode.SUCCESS)
    
    logger.info(f"Found {len(session_files)} chat session files")
    
    sessions = []
    for session_file in session_files:
        try:
            session = ChatSession.from_file(session_file)
            if session:
                sessions.append(session)
                success_count += 1
                logger.debug(f"Parsed {session_file.name}: {len(session.messages)} messages")
            else:
                error_count += 1
        except Exception as e:
            # Catch unexpected errors to prevent crash
            logger.error(f"Unexpected error parsing {session_file}: {e}")
            error_count += 1
    
    # Report summary
    logger.info(f"Successfully parsed {success_count} sessions")
    if error_count > 0:
        logger.warning(f"Failed to parse {error_count} sessions")
    
    # Output results
    try:
        if args.format == "json":
            output_json(sessions, args.output)
        else:
            output_html(sessions, args.output)
    except OSError as e:
        error_and_exit(
            f"Cannot write output file: {e}",
            ExitCode.OUTPUT_ERROR
        )
    
    # Exit with appropriate code
    if error_count > 0:
        sys.exit(ExitCode.PARTIAL_SUCCESS)
    else:
        sys.exit(ExitCode.SUCCESS)


# User-friendly error formatting
def format_error_message(operation: str, file_path: Path, error: Exception) -> str:
    """
    Format error message with context for end users.
    
    Technical details + plain language explanation + suggested action.
    """
    # Technical details
    details = f"{type(error).__name__}: {error}"
    
    # Plain language explanation
    if isinstance(error, PermissionError):
        explanation = "You don't have permission to access this file."
        suggestion = "Check file permissions or run with appropriate privileges."
    elif isinstance(error, FileNotFoundError):
        explanation = "The file could not be found."
        suggestion = "Verify the path is correct."
    elif isinstance(error, json.JSONDecodeError):
        explanation = "The file contains invalid JSON syntax."
        suggestion = "Check if the file is corrupted or incomplete."
    else:
        explanation = "An unexpected error occurred."
        suggestion = "Please report this issue with the file path and error details."
    
    return (
        f"Error {operation} '{file_path}':\n"
        f"  {details}\n"
        f"  {explanation} {suggestion}"
    )


# Example usage
def safe_parse_with_friendly_errors(file_path: Path) -> dict | None:
    """Parse JSON with user-friendly error messages."""
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        error_msg = format_error_message("parsing", file_path, e)
        logger.error(error_msg)
        return None
```

**Key Patterns**:
- Use `logging` module for all diagnostic output, never print errors
- Configure logging in `main()` based on `--verbose` flag
- Define exit codes as IntEnum for type safety and documentation
- Always include file path in error messages
- Use logger.error() for errors, logger.warning() for warnings, logger.info() for progress
- Write data to stdout, diagnostics to stderr (enables piping)
- Track success/error counts and report summary at end
- Catch `Exception` only at top level (main) to prevent crashes, be specific elsewhere

**Exit code conventions**:
- 0: Complete success, no errors
- 1: General error (unexpected failure)
- 2: Usage error (invalid arguments) - argparse uses this
- 3+: Application-specific errors (input error, output error, partial success)
- Non-zero indicates failure to shell scripts (`if cmd; then ... fi`)

**Logging levels**:
- ERROR: Fatal issues preventing operation (file not found, parse failure)
- WARNING: Non-fatal issues that don't block processing (skipped files, recoverable errors)
- INFO: Progress updates (files found, parsing stats)
- DEBUG: Detailed diagnostic info (per-file details, timing)

**Gotchas**:
- Don't use `print()` for errors—breaks when stdout is redirected
- `sys.exit()` raises `SystemExit` exception—caught by pytest, handle appropriately
- Logger configuration is global—call `setup_logging()` once in `main()`
- Don't use `logger = logging.getLogger(__name__)` at module level before configuration
- Exit code 2 is conventional for usage errors (argparse uses it)

---

## Summary Recommendations

**For your chat history parser project**:

1. **argparse**: Use dedicated parser function, Path types, choices validation, RawDescriptionHelpFormatter for examples
2. **pathlib**: Use rglob() for scanning, explicit error handling per exception type, validate writeability before processing
3. **JSON parsing**: Use dataclasses with from_dict() methods, parse at message level (granular), attempt partial recovery from errors
4. **pytest**: Use tmp_path fixtures, parametrize tests, test both success and error paths, integration tests for CLI
5. **Error handling**: Use logging module with stderr handler, define specific exit codes, preserve full context in messages

**Quick wins**:
- Start with argparse skeleton and basic path validation
- Write fixtures in conftest.py for reusable test data
- Implement ChatMessage and ChatSession dataclasses early
- Set up logging before any file operations
- Test with real VS Code chatSessions files early

**Avoid**:
- Adding external dependencies (pydantic, click, rich) before profiling shows need
- Catching broad Exception during parsing (be specific)
- Using print() for errors (use logging to stderr)
- All-or-nothing parsing (parse what's valid, skip what's corrupted)
- Creating temp files for testing (use tmp_path fixture)

# CLI Contract: chat-history

**Version**: 1.0.0  
**Date**: 2026-03-31  
**Type**: Command-Line Interface  
**Purpose**: Define the public interface contract for the VS Code Chat History Parser CLI tool

---

## Command Signature

```bash
chat-history [WORKSPACE_PATH] [OPTIONS]
```

---

## Positional Arguments

### WORKSPACE_PATH

**Type**: String (file system path)  
**Required**: No (defaults to OS-specific VS Code location)  
**Description**: Path to VS Code WorkspaceStorage directory containing chatSessions data

**Default Behavior** (when not provided):
- **Windows**: `%APPDATA%\Code\User\workspaceStorage`
- **macOS**: `$HOME/Library/Application Support/Code/User/workspaceStorage`
- **Linux**: `$HOME/.config/Code/User/workspaceStorage`

**Valid Examples**:
```bash
# Use default VS Code location
chat-history --list-workspaces
chat-history -o output.html

# Use explicit path
chat-history ~/.config/Code/User/workspaceStorage/abc123def456...
chat-history /home/user/.config/Code/User/workspaceStorage/ff0a29140064c53adb63a0d2383e841c
chat-history ../workspaceStorage/abc123
```

**Validation**:
- Path must exist
- Path must be a directory
- Path must be readable
- Path may contain wildcard for workspace ID if shell expands it

**Error Codes**:
- `1`: Default path does not exist (when no path provided)
- `1`: Path does not exist
- `1`: Path is not a directory
- `1`: Permission denied reading path
- `2`: Could not determine default path for OS

---

## Optional Arguments

### `-f, --format {json,html}`

**Type**: Choice (enum)  
**Default**: `json`  
**Description**: Output format for parsed chat history

**Values**:
- `json`: Structured JSON output to stdout or file
- `html`: Styled HTML output to file (with TailwindCSS)

**Examples**:
```bash
chat-history ~/workspace/abc123 -f json          # JSON to stdout
chat-history ~/workspace/abc123 --format html    # HTML to file
```

---

### `-o, --output PATH`

**Type**: String (file system path - file or directory)  
**Default**: 
- `stdout` for JSON format
- `chat-history.html` for HTML format

**Description**: Output file path or directory for generated content

**Behavior**:
- **If PATH is a directory**: Files are placed inside as `{workspace}.{ext}` 
  - Example: `-o output/` creates `output/ProjectA.html`, `output/ProjectB.html`
- **If PATH is a file**: Files use the path as a prefix: `{path}-{workspace}.{ext}`
  - Example: `-o report.html` creates `report-ProjectA.html`, `report-ProjectB.html`
- For JSON: If omitted, write to stdout; if provided, write to file(s)
- For HTML: If omitted, write to `chat-history.html`; if provided, write to specified path(s)
- Overwrites existing files without warning
- Creates parent directories if they don't exist

**Examples**:
```bash
# File prefix mode (default)
chat-history ~/workspace -o output.json
  → Creates: output-ProjectA.json, output-ProjectB.json

# Directory mode
chat-history ~/workspace -o output/
  → Creates: output/ProjectA.html, output/ProjectB.html

# With single workspace
chat-history ~/workspace/abc123 -f html -o /tmp/history.html
  → Creates: /tmp/history-ProjectName.html

# Directory with subdirectory creation
chat-history ~/workspace -o results/html/
  → Creates: results/html/ directory, then results/html/ProjectA.html
```

---

### `-m, --html-mode {single,per-session,per-workspace}`

**Type**: Choice (enum)  
**Default**: `single`  
**Description**: HTML file structure when using HTML output format

**Values**:
- `single`: All sessions in one HTML file with table of contents
- `per-session`: One HTML file per chat session
- `per-workspace`: One HTML file per workspace (groups sessions)

**Behavior**:
- Only applies when `-f html` is specified
- Ignored for JSON output
- `single` mode creates one file at output path
- `per-session` and `per-workspace` modes create a directory with multiple files

**Examples**:
```bash
chat-history ~/workspace/abc123 -f html -m single          # One file
chat-history ~/workspace/abc123 -f html -m per-session     # session-*.html files
chat-history ~/workspace/abc123 -f html -m per-workspace   # workspace-*.html files
```

---

### `-c, --concatenate`

**Type**: Boolean flag  
**Default**: `false`  
**Description**: Merge all sessions chronologically into a single conversation

**Behavior**:
- Sorts all messages across all sessions by timestamp
- Useful for viewing conversation history as a continuous timeline
- Works with both JSON and HTML formats
- May interleave messages from different sessions if timestamps overlap

**Examples**:
```bash
chat-history ~/workspace/abc123 -c                   # Concatenated JSON to stdout
chat-history ~/workspace/abc123 -f html -c -m single # Single HTML with all messages merged
```

---

### `-w, --workspace WORKSPACE_ID`

**Type**: String (32-character hex string)  
**Default**: None (processes all workspaces)  
**Description**: Filter to a specific workspace by its ID (directory name)

**Behavior**:
- Only processes sessions from the specified workspace ID
- Workspace ID is the 32-character hex directory name (e.g., `ff0a29140064c53adb63a0d2383e841c`)
- Exits with error code 1 if specified workspace not found
- Mutually exclusive with `--workspace-path` (use one or the other)

**Examples**:
```bash
chat-history ~/workspaceStorage -w ff0a29140064c53adb63a0d2383e841c -o output.html
```

---

### `-p, --workspace-path PATH`

**Type**: String (file system path or project name)  
**Default**: None (processes all workspaces)  
**Description**: Filter workspaces by matching the folder path from workspace.json

**Behavior**:
- Matches against the `folder` field in each workspace's `workspace.json` file
- Supports both full paths (e.g., `/home/user/Projects/LycheeOrg`) and partial names (e.g., `LycheeOrg`)
- Case-insensitive substring matching
- Processes all workspaces that match the search string
- Exits with error code 1 if no matching workspaces found
- Mutually exclusive with `--workspace` (use one or the other)

**Examples**:
```bash
# Filter by project name (partial match)
chat-history ~/workspaceStorage --workspace-path "LycheeOrg" -o output.html

# Filter by full path
chat-history ~/workspaceStorage -p "/home/user/Projects/LycheeOrg" -o output.html

# Case-insensitive matching
chat-history ~/workspaceStorage -p "lychee" -o output.html
```

**Note**: The workspace path filtering uses the folder path from workspace.json with the `file://` prefix removed. For example, `{"folder": "file:///home/user/Projects/LycheeOrg"}` becomes `/home/user/Projects/LycheeOrg` for matching purposes.

---

### `-l, --list-workspaces`

**Type**: Boolean flag  
**Description**: List all discovered workspaces in a human-readable table format and exit

**Behavior**:
- Scans the provided path for all valid workspaces
- Displays a table with workspace ID, session count, and project path
- Project path is extracted from workspace.json (with `file://` prefix removed)
- Shows "(no workspace.json)" for workspaces without a workspace.json file
- Exits immediately after displaying the list (does not parse or generate output)
- Exit code 0 on success, 1 if no workspaces found

**Examples**:
```bash
# List all workspaces in a directory
chat-history ~/.config/Code/User/workspaceStorage --list-workspaces

# List single workspace
chat-history ~/workspaceStorage/abc123... -l
```

**Expected Output**:
```
Found 3 workspace(s):

Workspace ID                       Sessions   Project Path
----------------------------------------------------------------------------------------------------
ff0a29140064c53adb63a0d2383e841c   42         /home/user/Documents/Projects/LycheeOrg
abc123def456789012345678901234ab   8          /home/user/Projects/ChatHistoryParser
def456abc789012345678901234567cd   15         /home/user/Documents/Projects/AnotherProject
```

---

### `-h, --help`

**Type**: Boolean flag  
**Description**: Display help message and exit

**Output**: Prints usage information to stdout, exits with code 0

**Example**:
```bash
chat-history --help
```

**Expected Output**:
```
usage: chat-history WORKSPACE_PATH [OPTIONS]

Parse VS Code WorkspaceStorage chat sessions

positional arguments:
  workspace_path        Path to VS Code WorkspaceStorage directory

optional arguments:
  -f, --format {json,html}
                        Output format (default: json)
  -o, --output PATH     Output file path
  -m, --html-mode {single,per-session,per-workspace}
                        HTML file structure mode (default: single)
  -c, --concatenate     Merge all sessions chronologically
  -w, --workspace WORKSPACE_ID
                        Filter to specific workspace ID
  -p, --workspace-path PATH
                        Filter workspaces by folder path
  -l, --list-workspaces List all workspaces and exit
  -h, --help            Show this help message and exit
  -v, --version         Show version number and exit

Example:
  chat-history ~/.config/Code/User/workspaceStorage/abc123 -f html
```

---

### `-v, --version`

**Type**: Boolean flag  
**Description**: Display version number and exit

**Output**: Prints version to stdout, exits with code 0

**Example**:
```bash
chat-history --version
```

**Expected Output**:
```
chat-history 1.0.0
```

---

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `0` | Success | All sessions parsed successfully, output generated |
| `1` | User Error | Invalid arguments, path not found, permission denied |
| `2` | Data Error | One or more sessions failed to parse (partial success) |
| `130` | Interrupted | User interrupted with Ctrl+C |

---

## Standard Streams

### stdout

**JSON Format** (default):
- Structured JSON output (unless `-o` specifies a file)
- Pretty-printed with 2-space indentation
- UTF-8 encoding

**HTML Format**:
- No stdout output (writes to file)
- Only status messages to stderr

### stderr

**Always used for**:
- Warning messages (malformed files, missing data)
- Error messages (file not found, permission denied, JSON decode errors)
- Progress summaries (e.g., "Parsed 42 sessions successfully")
- Parsing failure details (file path, error description)

**Format**: `{Level}: {Description}: {Context}`

**Examples**:
```
Warning: Malformed JSON in ff0a291.json: Expecting value at line 45
Error: Path does not exist: /invalid/path
Parsed 10 sessions successfully
Failed to parse 2 sessions
```

### stdin

Not used. All input is via command-line arguments and file system.

---

## Output Format Contracts

### JSON Output Schema

**Complete Schema**:
```json
{
  "metadata": {
    "generated_at": "string (ISO 8601 timestamp)",
    "workspace_path": "string (absolute path)",
    "session_count": "integer (non-negative)",
    "total_messages": "integer (non-negative)",
    "parse_errors": [
      {
        "file_path": "string (absolute path to failed file)",
        "error_type": "string (error category)",
        "message": "string (human-readable error description)"
      }
    ]
  },
  "sessions": [
    {
      "session_id": "string (unique identifier)",
      "creation_date": "string (ISO 8601) | null",
      "messages": [
        {
          "content": "string (non-empty)",
          "timestamp": "string (ISO 8601) | null",
          "role": "string (user | assistant)"
        }
      ]
    }
  ]
}
```

**Field Descriptions**:
- `metadata.generated_at`: When the JSON was generated (ISO 8601 format with timezone)
- `metadata.workspace_path`: Absolute path to the parsed workspace directory
- `metadata.session_count`: Number of successfully parsed sessions
- `metadata.total_messages`: Total message count across all sessions
- `metadata.parse_errors`: Array of errors encountered (empty if no errors)
- `sessions`: Array of successfully parsed chat sessions
- `session_id`: Unique identifier from chatSessions JSON file
- `creation_date`: When the session was created (may be null if parsing failed)
- `messages`: Ordered array of conversation messages (chronological)
- `content`: Message text (may include special formatting or JSON for tool invocations)
- `timestamp`: When message was sent (ISO 8601 with timezone, may be null if parsing failed)
- `role`: Message author (`user` or `assistant`)

**Example Output**:
```json
{
  "metadata": {
    "generated_at": "2026-03-31T22:44:40.714106",
    "workspace_path": "/home/user/.config/Code/User/workspaceStorage/abc123",
    "session_count": 2,
    "total_messages": 45,
    "parse_errors": [
      {
        "file_path": "/home/user/.config/Code/User/workspaceStorage/abc123/chatSessions/corrupted.json",
        "error_type": "JSONDecodeError",
        "message": "Expecting value: line 10 column 5 (char 234)"
      }
    ]
  },
  "sessions": [
    {
      "session_id": "1a7b49f7-eaca-4f0d-9ac8-4aaefa090e95",
      "creation_date": "2026-03-31T10:30:00.000000",
      "messages": [
        {
          "content": "How do I parse JSON in Python?",
          "timestamp": "2026-03-31T10:30:15.423000",
          "role": "user"
        },
        {
          "content": "You can use the json module in Python...",
          "timestamp": "2026-03-31T10:30:20.156000",
          "role": "assistant"
        }
      ]
    }
  ]
}
```

**Guarantees**:
- Valid JSON structure (parseable by any JSON parser)
- ISO 8601 timestamps for all dates (with microsecond precision)
- `messages` array ordered chronologically within each session
- `sessions` array ordered by creation date (oldest first)
- All string fields are UTF-8 encoded
- `null` values only for optional `creation_date` and `timestamp` fields
- Empty arrays (`[]`) for parse_errors and messages if none exist
- Indented with 2 spaces for human readability

### HTML Output Contract

**Structure**:
- Valid HTML5 markup
- Responsive layout (mobile-friendly)
- Self-contained (TailwindCSS loaded via CDN)
- Dark mode support (respects system preference)
- UTF-8 encoding
- Viewable offline after initial CDN load

**Required Elements**:
- `<header>`: Page title, generation timestamp
- `<nav>`: Table of contents (for single-file mode)
- `<main>`: Content sections for each session
- `<section id="session-{id}">`: Individual session container
- `<time>`: Semantic timestamp elements
- `<div class="message">`: Individual message containers

**Accessibility**:
- Semantic HTML5 elements
- `lang` attribute on `<html>` tag
- Proper heading hierarchy (h1 → h2 → ...)
- ARIA labels where appropriate
- Readable font sizes and contrast ratios

---

## Behavior Guarantees

### Idempotency

Running the command multiple times with the same inputs produces identical output (deterministic).

**Exception**: `generated_at` timestamp in metadata will differ.

### File Safety

- Does NOT modify source chatSessions files (read-only)
- Overwrites output files without warning
- Creates parent directories for output path if needed
- Does NOT follow symbolic links in workspace paths

### Error Resilience

- Continues parsing after individual file errors
- Reports all errors at completion
- Produces partial output (only successfully parsed sessions)
- Exit code 2 indicates partial success

### Performance

- Parses 10-100 sessions in <5 seconds (baseline target)
- No artificial limits on session count
- Memory usage scales linearly with data size
- Handles sessions with 1000+ messages

---

## Compatibility

### Python Version

**Minimum**: Python 3.12+

**Validation**: Command will error if run on Python <3.12

### Platform Support

- **Linux**: Primary development target
- **macOS**: Supported (different WorkspaceStorage path)
- **Windows**: Supported (different path conventions)

**WorkspaceStorage Paths**:
- Linux: `~/.config/Code/User/workspaceStorage/`
- macOS: `~/Library/Application Support/Code/User/workspaceStorage/`
- Windows: `%APPDATA%\Code\User\workspaceStorage\`

### VS Code Compatibility

**chatSessions Schema**: Version 3 (current as of 2026)

**Forward Compatibility**:
- Gracefully handles unknown schema fields (ignores them)
- Defensive parsing allows for schema evolution

**Backward Compatibility**:
- May work with schema v2 or earlier (not guaranteed)
- Will attempt to parse but may produce empty message lists

---

## Examples

### Basic Usage

```bash
# Parse workspace, output JSON to stdout
chat-history ~/.config/Code/User/workspaceStorage/abc123

# Parse workspace, output HTML to file
chat-history ~/.config/Code/User/workspaceStorage/abc123 -f html

# Parse workspace, output JSON to file
chat-history ~/.config/Code/User/workspaceStorage/abc123 -o history.json
```

### Advanced Usage

```bash
# Generate single HTML file with all sessions concatenated
chat-history ~/workspace/abc123 -f html -c -o full-history.html

# Generate per-session HTML files in output directory
chat-history ~/workspace/abc123 -f html -m per-session -o output/

# Parse multiple workspaces (using shell globbing)
for ws in ~/.config/Code/User/workspaceStorage/*/; do
  chat-history "$ws" -o "$(basename $ws).json"
done
```

### Pipeline Integration

```bash
# Filter JSON output with jq
chat-history ~/workspace/abc123 | jq '.sessions[] | select(.session_id == "target")'

# Count total messages across all sessions
chat-history ~/workspace/abc123 | jq '.metadata.total_messages'

# Convert JSON to CSV (using external tool)
chat-history ~/workspace/abc123 | jq -r '.sessions[].messages[] | [.timestamp, .role, .content] | @csv'
```

---

## Breaking Changes Policy

This contract follows semantic versioning:

- **Major version** (2.0.0): Breaking changes to CLI interface or output schema
- **Minor version** (1.1.0): New flags or features (backward compatible)
- **Patch version** (1.0.1): Bug fixes only

**Guaranteed Stability** (until 2.0.0):
- Positional argument order
- Flag names and short aliases
- JSON output schema (field names and types)
- Exit codes
- Error message format

**May Change in Minor Versions**:
- Additional optional flags
- New output modes
- Extended JSON metadata fields (additive only)

---

## Comprehensive Usage Examples

### Basic Usage with Default Path

```bash
# List all workspaces from default VS Code location
chat-history --list-workspaces

# Parse default location and output to HTML files (one per workspace)
chat-history -o output.html

# Parse default location and output JSON to stdout
chat-history --format json

# Parse default location with specific project filter
chat-history -p "LycheeOrg" -o output.html
```

### Basic Usage with Explicit Path

```bash
# Parse single workspace to HTML
chat-history ~/.config/Code/User/workspaceStorage/abc123... -o output.html

# Parse all workspaces to JSON
chat-history ~/.config/Code/User/workspaceStorage --format json -o output.json
```

### Filtering and Selection

```bash
# Filter by workspace ID
chat-history -w ff0a29140064c53adb63a0d2383e841c -o output.html

# Filter by project path (partial match, case-insensitive)
chat-history -p "LycheeOrg" -o lychee.html
chat-history -p "/home/biv/Documents/Projects/LycheeOrg" -o lychee.html

# List workspaces matching a path
chat-history -p "Lychee" --list-workspaces
```

### Advanced Options

```bash
# Concatenate all sessions chronologically
chat-history --concatenate -o merged.html

# Multiple filters: specific workspace with concatenation
chat-history -w abc123... --concatenate -o full-history.html

# JSON output to file
chat-history --format json -o data.json
```

### Pipeline and Automation

```bash
# Pipe JSON to jq for analysis
chat-history --format json | jq '.metadata'

# Count total messages across all workspaces
chat-history -f json | jq '.metadata.total_messages'

# Extract session IDs
chat-history -f json | jq '.sessions[].session_id'

# Filter and format in pipeline
chat-history -p "MyProject" -f json | jq '.sessions[] | {id: session_id, msg_count: (.messages | length)}'
```

---

## Testing Contract

Users can verify contract compliance by running:

```bash
# Check version
chat-history --version
# Expected: chat-history 1.0.0

# Validate JSON output schema
chat-history ~/workspace/abc123 | python3 -m json.tool
# Expected: Valid JSON with no errors

# Verify exit codes
chat-history /nonexistent/path; echo $?
# Expected: 1

chat-history ~/workspace/abc123 > /dev/null; echo $?
# Expected: 0
```

---

## Summary

**Interface Type**: POSIX-compliant CLI  
**Required Arguments**: 0 (workspace path defaults to OS-specific VS Code location)  
**Optional Arguments**: 1 (workspace path)  
**Optional Flags**: 7 (-f, -o, -m, -c, -w, -p, -l, -h, -v)  
**Output Formats**: 2 (JSON, HTML)  
**Exit Codes**: 4 (0, 1, 2, 130)  
**Platform Support**: Linux, macOS, Windows  
**Default Paths**:
- Linux: `$HOME/.config/Code/User/workspaceStorage`
- macOS: `$HOME/Library/Application Support/Code/User/workspaceStorage`
- Windows: `%APPDATA%\Code\User\workspaceStorage`
**Stability**: Semantic versioning (1.0.0)

This contract defines the complete external interface for the VS Code Chat History Parser. All implementation details that do not affect this contract are internal and subject to change.

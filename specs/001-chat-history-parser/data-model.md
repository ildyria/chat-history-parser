# Data Model: VS Code Chat History Parser

**Phase**: 1 - Design & Contracts  
**Date**: 2026-03-31  
**Purpose**: Define core entities, relationships, and state transitions

---

## Core Entities

### 1. WorkspaceContext

**Description**: Represents a VS Code workspace directory containing chat session data.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `workspace_id` | `str` | Yes | 32-character hex identifier from directory name | Regex: `^[0-9a-f]{32}$` |
| `base_path` | `Path` | Yes | Absolute path to workspaceStorage directory | Must exist and be readable |
| `session_files` | `list[Path]` | Yes | List of chatSessions JSON file paths | Empty list if no sessions found |

**Source**: Derived from file system structure `workspaceStorage/<workspace_id>/chatSessions/*.json`

**Relationships**:
- **Has many** ChatSession entities (one per JSON file)

**State Transitions**: None (immutable after discovery)

**Validation Rules**:
- `base_path` must exist as a directory
- `base_path` must be readable
- `workspace_id` must match hex pattern if derived from path
- `session_files` paths must match pattern `*/chatSessions/*.json`

---

### 2. ChatSession

**Description**: Represents a single chat conversation from a chatSessions JSON file.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `session_id` | `str` | Yes | Unique identifier from JSON `sessionId` field | Non-empty string |
| `creation_date` | `datetime` | No | Session creation timestamp from JSON | ISO 8601 format |
| `source_file` | `Path` | Yes | Path to source JSON file | Must exist |
| `messages` | `list[Message]` | Yes | Ordered list of conversation messages | Empty list if no valid messages |
| `parse_errors` | `list[str]` | Yes | List of parsing error descriptions | Empty if no errors |

**Source**: Parsed from chatSessions JSON schema v3:
```json
{
  "version": 3,
  "sessionId": "...",
  "creationDate": "...",
  "lastMessageDate": "...",
  "requests": [...]
}
```

**Relationships**:
- **Belongs to** WorkspaceContext (via source file path)
- **Has many** Message entities

**State Transitions**:
```
[File Discovered] → [Parsing] → [Parsed Successfully] | [Parsing Failed]
                                        ↓                      ↓
                                  [Has Messages]         [Has Errors]
```

**Validation Rules**:
- `session_id` must be present and non-empty
- `messages` list must maintain chronological order
- `creation_date` must be valid ISO 8601 or None
- `parse_errors` should document any schema deviations

---

### 3. Message

**Description**: Individual message in a chat conversation (minimal metadata per clarification Q&A).

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `content` | `str` | Yes | Message text content | Non-empty string after whitespace strip |
| `timestamp` | `datetime` | Yes | When message was sent | Valid datetime object |
| `role` | `str` | Yes | Speaker role | Must be 'user' or 'assistant' |

**Source**: Extracted from chatSessions JSON requests array:
- **User messages**: Extracted from `request.message` field
- **Assistant messages**: Extracted from `request.response[]` array (mixed types)
  - Text responses: `response[].value` (string)
  - Tool invocations: Flattened to text representation
  - Code blocks: Content extracted and formatted
  - Confirmations: Converted to text description

**Relationships**:
- **Belongs to** ChatSession
- Messages within a session are linearly ordered (no threading or replies)

**State Transitions**: None (immutable after extraction)

**Validation Rules**:
- `content` must not be empty after stripping whitespace
- `timestamp` must be a valid datetime (fallback to session creation date if missing)
- `role` must be exactly 'user' or 'assistant' (lowercase)

**Extraction Strategy for Heterogeneous Responses**:
```python
# chatSessions v3 response array contains mixed types:
response = [
    {"value": "text"},           # → Message content
    {"kind": "tool", ...},       # → Flatten to text description
    {"kind": "codeBlock", ...},  # → Extract code with language
    {"kind": "confirmation", ...} # → Convert to text
]
```

Implementation must flatten all response types into readable text content.

---

## Data Flow

### Input → Parsing → Output

```
File System
    ↓
WorkspaceContext (discover workspace IDs and session files)
    ↓
ChatSession (parse JSON schema v3)
    ↓
Message[] (extract minimal fields: content, timestamp, role)
    ↓
Output Format (JSON or HTML)
```

### Parsing Pipeline

1. **Discovery Phase**:
   - Input: `Path` to workspaceStorage directory
   - Scan: `glob("*/chatSessions/*.json")`
   - Output: `list[Path]` of session files

2. **Extraction Phase**:
   - Input: Single chatSessions JSON file
   - Parse: JSON → dict with defensive access
   - Transform: Flatten `requests[].response[]` arrays
   - Output: `ChatSession` with `Message[]`

3. **Aggregation Phase**:
   - Input: `list[ChatSession]`
   - Filter: Remove sessions with no messages
   - Sort: Chronological order if `--concatenate` flag set
   - Output: Unified collection

4. **Serialization Phase**:
   - Input: Aggregated sessions
   - Transform: JSON serialization or HTML generation
   - Output: File or stdout

---

## Output Schemas

### JSON Output Format

```json
{
  "metadata": {
    "generated_at": "2026-03-31T12:00:00Z",
    "workspace_path": "/path/to/workspaceStorage/abc123",
    "session_count": 3,
    "total_messages": 42,
    "parse_errors": 0
  },
  "sessions": [
    {
      "session_id": "def456",
      "creation_date": "2026-03-30T10:00:00Z",
      "source_file": "abc123.json",
      "messages": [
        {
          "content": "Hello, how can I help?",
          "timestamp": "2026-03-30T10:00:01Z",
          "role": "user"
        },
        {
          "content": "I can assist with that.",
          "timestamp": "2026-03-30T10:00:02Z",
          "role": "assistant"
        }
      ]
    }
  ]
}
```

**Schema Notes**:
- Top-level `metadata` provides summary information
- `sessions` array contains all parsed conversations
- Each session includes minimal message data (per clarification)
- Timestamps are ISO 8601 strings
- No nested threading or reply chains (flat message list)

### HTML Output Structure

**Visual Design**: GitHub Copilot-style chat interface
- User messages: Right-aligned with standard text styling
- Assistant actions/tools: Left-aligned with muted background (gray/neutral)
- Assistant thinking: Left-aligned with muted background  
- Assistant responses: Left-aligned with standard contrast

**Single File Mode** (`--html-mode single`):
```html
<html>
  <head>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-gray-50">
    <header class="bg-white shadow">
      <h1>Chat History</h1>
      <p>Generated: 2026-03-31</p>
    </header>
    <nav class="sticky top-0 bg-white border-b">
      <!-- Table of contents with links to sessions -->
    </nav>
    <main class="max-w-4xl mx-auto py-8">
      <section id="session-1" class="mb-12">
        <h2 class="text-2xl font-bold mb-4">Session 1</h2>
        <!-- User message: right-aligned -->
        <div class="flex justify-end mb-4">
          <div class="bg-blue-100 rounded-lg p-4 max-w-xl">
            <p class="text-sm text-gray-500">2026-03-31 10:00:01</p>
            <p>User message content</p>
          </div>
        </div>
        <!-- Assistant response: left-aligned -->
        <div class="flex justify-start mb-4">
          <div class="bg-white border rounded-lg p-4 max-w-xl">
            <p class="text-sm text-gray-500">2026-03-31 10:00:02</p>
            <p>Assistant response content</p>
          </div>
        </div>
        <!-- Assistant action/tool: left-aligned, muted -->
        <div class="flex justify-start mb-4">
          <div class="bg-gray-100 border rounded-lg p-4 max-w-xl">
            <p class="text-sm text-gray-400">Tool Invocation</p>
            <p class="text-gray-600">Action description</p>
          </div>
        </div>
      </section>
    </main>
  </body>
</html>
```

**Per-Session Mode** (`--html-mode per-session`):
- Multiple files: `session-<session_id>.html`
- Each file contains one session with its messages
- Index file: `index.html` with links to all session files

**Per-Workspace Mode** (`--html-mode per-workspace`):
- Multiple files: `workspace-<workspace_id>.html`
- Each file groups all sessions from that workspace
- Index file: `index.html` with links to all workspace files

---

## Error Handling Model

### ParseError Entity

**Description**: Records errors encountered during parsing without halting execution.

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `Path` | Source file that caused error |
| `error_type` | `str` | Category: 'json_decode', 'permission', 'io_error', 'schema_invalid' |
| `description` | `str` | Human-readable error message |
| `context` | `str` | Additional context (line number, field name, etc.) |

**Usage**: Collected in `ChatSession.parse_errors` list, reported to stderr at end.

### Partial Success Strategy

- **Continue on error**: If one session fails, parse remaining sessions
- **Report all errors**: Aggregate errors at end, write to stderr
- **Exit code 2**: Indicates partial failure (some sessions parsed, some failed)
- **Success criteria**: At least one session parsed successfully

---

## Relationships Diagram

```
WorkspaceContext (1) ──────── (*) ChatSession
                                       │
                                       │ (1)
                                       │
                                       ↓
                                   Messages (*)
                                   [ordered list]

Legend:
  (1) = one
  (*) = zero or more
```

**Key Constraints**:
- Messages are ordered chronologically within a session
- Sessions belong to exactly one workspace
- No cross-session or cross-workspace relationships
- No user profiles or persistent identity across sessions

---

## Performance Considerations

### Memory Model

- **Eager loading**: Parse all sessions into memory before output generation
- **Trade-off**: Simplicity over memory efficiency
- **Justification**: Typical workspaces have <100 sessions, <10MB total data

**Alternative for Large Workspaces** (future optimization):
- Streaming: Parse one session at a time, write incrementally
- Only necessary if encountering workspaces with 1000+ sessions

### Indexing

No indexing required (file system is the index).

---

## Summary

**Total Entities**: 3 primary (WorkspaceContext, ChatSession, Message) + 1 error (ParseError)

**Relationships**: Simple tree hierarchy (workspace → sessions → messages)

**Constraints**:
- Immutable after parsing
- Chronologically ordered messages
- Defensive parsing with error collection

**Output Formats**:
- JSON: Structured data with metadata
- HTML: Three modes (single, per-session, per-workspace)

All entities align with constitution principles (single-purpose, minimal metadata, graceful error handling).

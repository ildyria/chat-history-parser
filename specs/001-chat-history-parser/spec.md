# Feature Specification: VS Code Chat History Parser

**Feature Branch**: `001-chat-history-parser`  
**Created**: 2026-03-31  
**Status**: Draft  
**Input**: User description: "Specify what we want"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parse and View Chat History (Priority: P1)

A developer wants to extract and view their chat conversations with GitHub Copilot that are stored in VS Code's WorkspaceStorage. They provide the path to their WorkspaceStorage directory, and the tool outputs a readable HTML file showing all conversations with timestamps, messages, and context.

**Why this priority**: This is the core value proposition - making chat history accessible and readable. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by running the CLI with a WorkspaceStorage path containing chat data and verifying an HTML file is generated with correct content. Delivers immediate value by making hidden chat history visible.

**Acceptance Scenarios**:

1. **Given** a valid WorkspaceStorage directory path with chat session data, **When** user runs the parser with HTML output format, **Then** a styled HTML file is generated containing all chat messages with timestamps and proper formatting
2. **Given** multiple chat sessions in the WorkspaceStorage, **When** parser processes the directory, **Then** all sessions are included in the output ordered by timestamp
3. **Given** a generated HTML file, **When** user opens it in a browser, **Then** conversations are displayed with TailwindCSS styling, readable typography, and proper message threading

---

### User Story 2 - Export for Programmatic Processing (Priority: P2)

A developer wants to analyze their chat history programmatically (e.g., count tokens, extract code snippets, build analytics). They run the parser with JSON output to get structured data they can process with scripts or other tools.

**Why this priority**: Enables automation and integration with other tools. Important for power users but not essential for basic viewing functionality.

**Independent Test**: Can be tested by running the CLI with JSON output flag and validating the output against a JSON schema. Delivers value by enabling programmatic analysis without requiring HTML parsing.

**Acceptance Scenarios**:

1. **Given** a valid WorkspaceStorage directory path, **When** user runs the parser with JSON output format flag, **Then** structured JSON is written to stdout with proper schema
2. **Given** JSON output from the parser, **When** user pipes it to another tool (e.g., jq, Python script), **Then** the data is valid and parseable with documented schema structure
3. **Given** multiple chat sessions, **When** JSON output is generated, **Then** each session includes metadata (workspace, timestamps, message count) and full message arrays

---

### User Story 3 - Handle Multiple Workspaces (Priority: P3)

A developer has multiple VS Code workspaces and wants to parse chat history from a specific workspace or compare conversations across workspaces. They can target specific workspace folders within WorkspaceStorage or process multiple paths.

**Why this priority**: Useful for organization and comparison but not critical for basic functionality. Can be achieved by running the tool multiple times initially.

**Independent Test**: Can be tested by providing a WorkspaceStorage path containing multiple workspace folders and verifying the output correctly identifies and separates conversations by workspace.

**Acceptance Scenarios**:

1. **Given** a WorkspaceStorage path with multiple workspace folders, **When** parser processes the directory, **Then** output clearly identifies which workspace each conversation belongs to
2. **Given** a specific workspace identifier, **When** user provides a filter argument, **Then** only conversations from that workspace are included in output

---

### User Story 4 - Recover from Corrupted Data (Priority: P2)

A developer has chat history files that may be partially corrupted or incomplete. The parser should extract what's valid and clearly report what couldn't be processed, ensuring no data loss for recoverable conversations.

**Why this priority**: Real-world data is often imperfect. Graceful error handling is essential for reliability, though less critical than core parsing functionality.

**Independent Test**: Can be tested by providing a WorkspaceStorage path with intentionally corrupted chatSessions files and verifying the parser extracts valid data and reports specific errors.

**Acceptance Scenarios**:

1. **Given** a chatSessions file with valid and corrupted entries, **When** parser processes the file, **Then** valid entries are included in output and corrupted entries are reported to stderr with specific line numbers
2. **Given** a completely unreadable chatSessions file, **When** parser encounters it, **Then** an error message is written to stderr identifying the file and error type, and processing continues with other files
3. **Given** parsing completed with partial failures, **When** tool exits, **Then** exit code indicates partial success (non-zero) and stderr contains summary of what failed

---

### Edge Cases

- What happens when WorkspaceStorage path doesn't exist? (Clear error message, exit code 1)
- What happens when WorkspaceStorage directory exists but contains no chat session files? (Success with empty output, informational message)
- What happens when chatSessions files exist but are empty or contain no messages? (Include in output with zero messages, no error)
- What happens when messages contain special characters, code blocks, or malformed JSON? (Escape properly in HTML, preserve raw in JSON, continue parsing)
- What happens when output path is not writable or disk is full? (Error message before processing, fail fast)
- What happens when a chat session file is locked or in use by VS Code? (Skip with warning, continue with other files)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a WorkspaceStorage directory path as a required positional command-line argument (first argument after command name)
- **FR-002**: System MUST locate and parse all chatSessions files within the provided WorkspaceStorage path by scanning subdirectories matching pattern `<workspace-id>/chatSessions/<hex>.json` where workspace-id is a 32-character hex string and hex is a variable-length hex filename
- **FR-003**: System MUST extract message content, timestamps, participants (user/assistant), and workspace context from VS Code's chatSessions JSON format (version 3 schema with requests array containing request/response pairs)
- **FR-003a**: System MUST support concatenating multiple chat session files when user provides the option, merging conversations by timestamp order across all parsed files
- **FR-003b**: When parsing response arrays, system MUST extract text content from mixed response types (text responses, tool invocations, edits) and flatten into readable message content while discarding detailed tool metadata
- **FR-004**: System MUST support JSON output format via GNU-style command-line flag with both long and short options (`-f json` or `--format json`)
- **FR-005**: System MUST support HTML output format via GNU-style command-line flag with both long and short options (`-f html` or `--format html`), with HTML as the default if no format is specified
- **FR-006**: HTML output MUST include TailwindCSS styling via CDN for typography, spacing, colors, and responsive layout, using a GitHub Copilot-style chat interface design:
  - User messages positioned on the right side with standard text styling
  - Assistant tool invocations/actions positioned on the left side with muted background colors (gray/neutral tones)
  - Assistant thinking blocks positioned on the left side with muted background colors
  - Assistant responses positioned on the left side with standard contrast
  - Proper spacing, borders, and visual hierarchy to distinguish message types
- **FR-007**: HTML output MUST be self-contained (all files including CSS/JS via CDN) and viewable offline after generation, with user-configurable structure via CLI flag: single HTML file with all sessions (default) or one file per session/workspace
- **FR-008**: System MUST output parsed chat data to stdout (JSON format) or to a specified file path (HTML format)
- **FR-009**: System MUST write error messages and warnings to stderr with descriptive context (file path, error type, recovery action)
- **FR-010**: System MUST exit with code 0 on complete success, non-zero on any failure (partial or complete)
- **FR-011**: System MUST validate WorkspaceStorage path exists and is readable before attempting to parse
- **FR-012**: System MUST handle missing, malformed, or corrupted chatSessions files gracefully by parsing what's valid and reporting specific errors
- **FR-013**: System MUST preserve message ordering by timestamp within each conversation
- **FR-014**: System MUST identify and label which workspace each conversation belongs to when multiple workspaces exist
- **FR-015**: JSON output MUST conform to a documented schema with fields for sessions, messages, metadata, and timestamps
- **FR-016**: System MUST handle special characters, code blocks, and Unicode content correctly in both JSON and HTML output
- **FR-017**: Users MUST be able to specify output file path or directory via GNU-style command-line argument with both long and short options (`-o path/to/file.html` or `--output path/to/file.html` for single file, `--output path/to/dir/` for multi-file output)
- **FR-018**: System MUST provide a GNU-style CLI flag with both long and short options (`-m single` or `--html-mode single|per-session|per-workspace`) to control HTML output structure: single file with all sessions, one file per session, or one file per workspace
- **FR-018a**: System MUST provide a GNU-style CLI flag with both long and short options (`-c` or `--concatenate`) to merge multiple chat session files into a single chronological conversation stream ordered by timestamp
- **FR-019**: System MUST display help text showing usage, available flags, and examples via standard `-h` or `--help` flag
- **FR-020**: System MUST display version information via standard `-v` or `--version` flag

### Key Entities *(include if feature involves data)*

#### Source Data Structure (VS Code chatSessions JSON Schema v3)

The parser reads from VS Code's chatSessions files with the following structure:

- **Root Object**: Contains `version`, `requesterUsername`, `responderUsername`, `sessionId`, `creationDate`, `lastMessageDate`, `isImported`, and `requests[]` array
- **Request Object**: Each entry in `requests[]` contains `requestId`, `message` (user input with text/parts), `variableData`, `response[]` array, `responseId`, `result`, `timestamp`, `agent` details, and metadata
- **Response Parts**: Each `response[]` contains mixed types: text responses (with `value`), tool invocations (with `toolName`, `invocationMessage`), text edit groups (with `uri`, `edits`), confirmations, code blocks, etc.

**File Path Pattern**: `<WorkspaceStorage>/<workspace-id>/chatSessions/<hex>.json`  
- `<workspace-id>`: 32-character hex string identifying the VS Code workspace  
- `<hex>.json`: Variable-length hex filename for each chat session

#### Extracted Output Structure (Simplified Model)

The parser extracts and simplifies the complex source structure into:

- **ChatSession**: Represents a single conversation thread; contains:
  - `sessionId`: UUID from source file
  - `workspaceId`: Extracted from file path
  - `creationDate`: Timestamp when session started
  - `lastMessageDate`: Timestamp of last message
  - `requesterUsername`: User identifier
  - `responderUsername`: Assistant identifier (e.g., "GitHub Copilot")
  - `messages[]`: Array of Message objects

- **Message**: Individual message exchange extracted from request/response pairs; contains exactly three required fields to keep the data model minimal and focused:
  - `content`: Text content (from `message.text` for user, concatenated `response[].value` for assistant)
  - `timestamp`: Message timestamp
  - `role`: Either "user" or "assistant"
  
  Note: Complex response parts (tool invocations, edits, confirmations) are flattened into plain text for the message content. Detailed tool metadata is discarded.

- **WorkspaceContext**: Identifies the VS Code workspace; contains:
  - `workspaceId`: 32-character hex identifier extracted from file path
  - `sessionCount`: Number of chat sessions in this workspace
  
- **ParseResult**: Overall output structure; contains:
  - `sessions[]`: Collection of ChatSession objects
  - `metadata`: Parsing statistics (file count, message count, error count, start/end time)
  - `errors[]`: Array of error/warning objects with file path and description

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully parse a typical WorkspaceStorage directory (10-100 chat sessions) in under 5 seconds (baseline performance target; tool should handle any number of sessions without hard limits or warnings)
- **SC-002**: HTML output is readable and well-formatted in all major browsers (Chrome, Firefox, Safari, Edge) without additional configuration
- **SC-003**: Parser successfully extracts valid data from at least 95% of chat sessions in real-world WorkspaceStorage directories
- **SC-004**: Zero data loss occurs when parsing valid, well-formed chatSessions files
- **SC-005**: Error messages provide sufficient information for users to identify and resolve issues in under 2 minutes for common problems
- **SC-006**: JSON output conforms to documented schema 100% of the time and validates against JSON Schema validators
- **SC-007**: HTML files render correctly offline after generation with no broken styling or missing content
- **SC-008**: Users can install and run the tool from scratch (including dependencies via uv) in under 2 minutes

## Assumptions

- Users are running the tool on systems with Python 3.8+ available
- Users have permission to read their VS Code WorkspaceStorage directory (typically in user home directory)
- VS Code's chatSessions files follow version 3 schema with root-level `requests[]` array containing request/response pairs as discovered in actual WorkspaceStorage inspection
- VS Code's chatSessions file format remains stable or changes in backward-compatible ways (version field allows detection of schema changes)
- Chat session files are stored at `workspaceStorage/<workspace-id>/chatSessions/<hex>.json` path structure
- Response arrays contain heterogeneous types (text, tool invocations, edits, confirmations) that need flattening into readable text
- Users understand basic command-line interface usage and can provide file paths
- Internet connection is available during installation (to fetch uv and dependencies) but not required for running the parser
- TailwindCSS CDN remains accessible and stable (fallback: embedded CSS can be added if CDN fails)
- HTML output will be viewed in browsers with modern CSS support (2020+ browser versions)
- WorkspaceStorage directories are on local filesystem (not network drives or cloud storage)

## Clarifications

### Session 2026-03-31

- Q: VS Code chatSessions File Format → A: chatSessions format is undocumented and should be reverse-engineered from actual WorkspaceStorage inspection
- Q: HTML Output File Structure → A: User-configurable via CLI flag to choose single-file or multi-file output
- Q: Message Metadata Capture → A: Capture minimal metadata only (message content, timestamp, role) - no additional fields
- Q: Performance Target for Large Workspaces → A: No special handling needed; tool should handle any number of sessions without warnings
- Q: CLI Argument Structure → A: GNU-style long options with short aliases (e.g., `-f/--format`, `-o/--output`, `-h/--help`, `-v/--version`) and WorkspaceStorage path as required positional argument

### Session 2026-03-31 (Updated after studying actual chatSessions file)

- **Discovered File Structure**: Chat sessions are stored at `workspaceStorage/<workspace-id>/chatSessions/<hex>.json` with complex nested JSON containing version 3 schema with requests/response arrays
- **Data Extraction Strategy**: Parse complex nested structure (requests[], response[] with mixed types) but extract only minimal fields (content, timestamp, role) to simplified output model
- **Concatenation Requirement**: May need to support concatenating multiple chat session files, merging conversations by timestamp order for comprehensive history export

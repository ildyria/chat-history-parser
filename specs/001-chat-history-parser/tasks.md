# Tasks: VS Code Chat History Parser

**Input**: Design documents from `/specs/001-chat-history-parser/`  
**Prerequisites**: plan.md (required), spec.md (required), data-model.md (required), contracts/cli.md (required)

**Tests**: TDD is mandatory per Constitution Principle IV - all parsing logic must have tests written first

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, US3, US4) - required for user story phases only
- Include exact file paths in descriptions

## Path Conventions

Single-project Python CLI tool structure (per plan.md):
- `src/chat_history_parser/` - Application code
- `tests/` - Test code (unit/, integration/, contract/, fixtures/)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: src/chat_history_parser/, tests/{unit,integration,contract,fixtures}/
- [X] T002 Initialize Python 3.12+ project with uv package manager (pyproject.toml with project metadata)
- [X] T003 [P] Configure pytest in pyproject.toml with test discovery and coverage settings
- [X] T004 [P] Create src/chat_history_parser/__init__.py with package version (__version__ = "0.1.0")
- [X] T005 [P] Create src/chat_history_parser/__main__.py as CLI entry point (imports cli.main())
- [X] T006 [P] Create empty module files: src/chat_history_parser/{cli,parser,models,scanner,errors}.py
- [X] T007 [P] Create src/chat_history_parser/formatters/ directory with __init__.py, json_formatter.py, html_formatter.py
- [X] T008 Create tests/fixtures/ directory with sample chatSessions JSON files for testing
- [X] T009 [P] Create README.md with project overview, installation via uv, and usage examples
- [X] T010 [P] Create .gitignore for Python projects (__pycache__, *.pyc, .pytest_cache/, dist/, *.egg-info/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Define data models in src/chat_history_parser/models.py: WorkspaceContext, ChatSession, Message, ParseError dataclasses
- [X] T012 [P] Implement custom exception classes in src/chat_history_parser/errors.py: WorkspaceNotFoundError, InvalidSessionFileError, ParsingError
- [X] T013 Implement CLI argument parser in src/chat_history_parser/cli.py: GNU-style args (path, -f/--format, -o/--output, -m/--html-mode, -c/--concatenate, -h/--help, -v/--version)
- [X] T014 [P] Implement workspace scanner in src/chat_history_parser/scanner.py: discover_workspaces() and find_session_files() functions using pathlib
- [X] T015 Create test fixtures: tests/fixtures/sample-workspace/ with realistic chatSessions JSON files (valid, empty, malformed)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Parse and View Chat History (Priority: P1) 🎯 MVP

**Goal**: Parse WorkspaceStorage chatSessions files and generate readable HTML output with GitHub Copilot-style chat interface

**Independent Test**: Run CLI with test workspace path and verify HTML file generated with correct Copilot-style layout (user messages right, assistant messages left with appropriate styling)

### Tests for User Story 1 (TDD - Write First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US1] Unit test for chatSessions JSON parsing in tests/unit/test_parser.py: test_parse_session_v3_schema()
- [X] T017 [P] [US1] Unit test for message extraction in tests/unit/test_parser.py: test_extract_messages_minimal_fields()
- [X] T018 [P] [US1] Unit test for response flattening in tests/unit/test_parser.py: test_flatten_mixed_response_types()
- [X] T019 [P] [US1] Unit test for HTML generation in tests/unit/test_html_formatter.py: test_generate_single_file_html()
- [X] T020 [P] [US1] Unit test for Copilot-style message rendering in tests/unit/test_html_formatter.py: test_user_message_right_aligned(), test_assistant_message_left_aligned()
- [X] T021 [P] [US1] Integration test in tests/integration/test_parse_and_view.py: test_parse_workspace_generate_html()
- [X] T022 [P] [US1] Contract test in tests/contract/test_html_output.py: validate HTML structure, TailwindCSS CDN presence, message positioning

### Implementation for User Story 1

- [X] T023 [P] [US1] Implement parse_session_file() in src/chat_history_parser/parser.py: read JSON, validate v3 schema, extract sessionId/dates
- [X] T024 [P] [US1] Implement extract_user_message() in src/chat_history_parser/parser.py: extract content from request.message field
- [X] T025 [P] [US1] Implement extract_assistant_messages() in src/chat_history_parser/parser.py: flatten response[] array (text, tool, codeBlock, confirmation types)
- [X] T026 [P] [US1] Implement defensive JSON parsing with error recovery in src/chat_history_parser/parser.py: handle malformed files, log to stderr
- [X] T027 [US1] Implement HTMLFormatter class in src/chat_history_parser/formatters/html_formatter.py: __init__, generate() method
- [X] T028 [US1] Implement _generate_html_head() in html_formatter.py: TailwindCSS CDN script tag, meta tags, page title
- [X] T029 [US1] Implement _generate_header() in html_formatter.py: page title, generation timestamp, styling
- [X] T030 [US1] Implement _generate_session_section() in html_formatter.py: session header with ID and date
- [X] T031 [US1] Implement _render_user_message() in html_formatter.py: right-aligned div with bg-blue-100, timestamp, content
- [X] T032 [US1] Implement _render_assistant_message() in html_formatter.py: left-aligned div with bg-white border, timestamp, content
- [X] T033 [US1] Implement _detect_message_type() in html_formatter.py: identify tool invocations, thinking blocks from content patterns
- [X] T034 [US1] Implement _render_assistant_action() in html_formatter.py: left-aligned div with bg-gray-100 muted styling for tools/actions
- [X] T035 [US1] Implement message ordering by timestamp in src/chat_history_parser/parser.py: sort messages chronologically
- [X] T036 [US1] Wire HTML formatter in src/chat_history_parser/cli.py: call HTMLFormatter.generate() when --format html
- [X] T037 [US1] Implement file output to specified path in cli.py: write HTML to --output path, default to stdout if not specified
- [X] T038 [US1] Add error handling for file write failures in cli.py: catch IOError, write to stderr, exit code 1

**Checkpoint**: At this point, User Story 1 should be fully functional - parsing chatSessions and generating Copilot-style HTML

---

## Phase 4: User Story 2 - Export for Programmatic Processing (Priority: P2)

**Goal**: Generate structured JSON output for programmatic analysis and automation

**Independent Test**: Run CLI with --format json flag and validate output against JSON schema, pipe to jq to verify parseability

### Tests for User Story 2 (TDD - Write First)

- [X] T039 [P] [US2] Unit test in tests/unit/test_json_formatter.py: test_generate_json_output()
- [X] T040 [P] [US2] Contract test in tests/contract/test_json_schema.py: validate JSON schema compliance (metadata, sessions array, message fields)
- [X] T041 [P] [US2] Integration test in tests/integration/test_json_export.py: test_parse_to_json_stdout(), test_parse_to_json_file()

### Implementation for User Story 2

- [X] T042 [P] [US2] Implement JSONFormatter class in src/chat_history_parser/formatters/json_formatter.py: __init__, generate() method
- [X] T043 [US2] Implement _build_metadata() in json_formatter.py: generated_at, workspace_path, session_count, total_messages, parse_errors
- [X] T044 [US2] Implement _serialize_sessions() in json_formatter.py: convert ChatSession objects to dicts with minimal fields (content, timestamp, role)
- [X] T045 [US2] Implement _serialize_messages() in json_formatter.py: convert Message objects to dicts, ISO 8601 timestamps
- [X] T046 [US2] Wire JSON formatter in src/chat_history_parser/cli.py: call JSONFormatter.generate() when --format json, output to stdout by default
- [X] T047 [US2] Add JSON schema validation helper in tests/contract/json_schema_validator.py: validate_output_schema() function
- [X] T048 [US2] Document JSON schema in specs/001-chat-history-parser/contracts/cli.md: add JSON output format section with example

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (HTML and JSON outputs)

---

## Phase 5: User Story 4 - Recover from Corrupted Data (Priority: P2)

**Goal**: Gracefully handle malformed/corrupted chatSessions files by parsing valid data and reporting specific errors

**Independent Test**: Run CLI with workspace containing corrupted JSON files and verify partial success with detailed error messages on stderr

### Tests for User Story 4 (TDD - Write First)

- [X] T049 [P] [US4] Unit test in tests/unit/test_parser.py: test_handle_malformed_json(), test_handle_missing_required_fields()
- [X] T050 [P] [US4] Unit test in tests/unit/test_parser.py: test_recover_from_invalid_timestamps(), test_handle_empty_response_arrays()
- [X] T051 [P] [US4] Integration test in tests/integration/test_error_recovery.py: test_partial_parse_with_errors()

### Implementation for User Story 4

- [X] T052 [P] [US4] Implement try/except blocks with specific error handling in src/chat_history_parser/parser.py: json.JSONDecodeError → log and skip file
- [X] T053 [P] [US4] Implement defensive field access in parser.py: use dict.get() with defaults for optional fields (creationDate, etc.)
- [X] T054 [P] [US4] Implement timestamp validation and fallback in parser.py: try parsing ISO 8601, fallback to None on failure
- [X] T055 [US4] Implement error aggregation in parser.py: collect ParseError objects during parsing, attach to ChatSession.parse_errors
- [X] T056 [US4] Implement stderr logging for parse errors in cli.py: write descriptive error messages with file path and error type
- [X] T057 [US4] Implement partial success handling in cli.py: exit code 0 if any sessions parsed successfully, include error summary in output
- [X] T058 [US4] Add error reporting to HTML output in html_formatter.py: display parse errors in dedicated warning section with muted styling
- [X] T059 [US4] Add error reporting to JSON output in json_formatter.py: include parse_errors array in metadata section

**Checkpoint**: Parser now handles corrupted data gracefully while maximizing successful data extraction

---

## Phase 6: User Story 3 - Handle Multiple Workspaces (Priority: P3)

**Goal**: Identify and separate conversations by workspace when multiple workspace folders exist in WorkspaceStorage

**Independent Test**: Run CLI with WorkspaceStorage containing multiple workspace-id folders and verify output correctly identifies and labels each workspace

### Tests for User Story 3 (TDD - Write First)

- [X] T060 [P] [US3] Unit test in tests/unit/test_scanner.py: test_discover_multiple_workspaces(), test_workspace_id_extraction()
- [X] T061 [P] [US3] Integration test in tests/integration/test_multi_workspace.py: test_parse_multiple_workspaces_separate_labels()

### Implementation for User Story 3

- [X] T062 [P] [US3] Enhance discover_workspaces() in src/chat_history_parser/scanner.py: scan for multiple workspace-id directories (pattern: [0-9a-f]{32})
- [X] T063 [US3] Add workspace_id field to ChatSession in models.py: store workspace identifier with each session
- [X] T064 [US3] Update parse_session_file() in parser.py: pass workspace_id to ChatSession constructor
- [X] T065 [US3] Update HTML formatter in html_formatter.py: add workspace labels to session headers, group sessions by workspace in multi-workspace scenarios
- [X] T066 [US3] Update JSON formatter in json_formatter.py: include workspace_id in session metadata
- [X] T067 [US3] Add --workspace filter flag to cli.py: optional workspace-id argument to parse only specific workspace

**Checkpoint**: All user stories should now be independently functional, including multi-workspace support

---

## Phase 7: Advanced Output Modes

**Purpose**: Implement user-configurable HTML output structures

- [X] T068 [P] Implement --html-mode flag handling in src/chat_history_parser/cli.py: parse single|per-session|per-workspace argument
- [X] T069 Implement single-file mode in html_formatter.py: generate_single_file() - all sessions in one HTML with table of contents
- [X] T070 Implement per-session mode in html_formatter.py: generate_per_session() - one HTML file per session, index.html with links
- [X] T071 Implement per-workspace mode in html_formatter.py: generate_per_workspace() - one HTML per workspace, index.html with links  
- [X] T072 Implement --concatenate flag in cli.py: merge multiple sessions chronologically
- [X] T073 Implement session concatenation logic in parser.py: sort all messages from all sessions by timestamp, merge into single virtual session
- [X] T074 Add tests for multi-file output modes in tests/integration/test_output_modes.py: test_per_session_mode(), test_per_workspace_mode()

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, documentation, and user experience enhancements

- [X] T075 [P] Implement --help text in cli.py: comprehensive usage examples, all flags documented with short/long options
- [X] T076 [P] Implement --version in cli.py: display version from __version__, format: "chat-history-parser 0.1.0"
- [X] T077 [P] Add progress indicators for large workspaces in cli.py: optional stderr output showing "Parsing session 10/50..."
- [X] T078 [P] Implement exit code documentation in cli.py: 0=success, 1=error, 2=invalid args, 130=interrupted
- [X] T079 [P] Add CSS enhancements to html_formatter.py: responsive design for mobile devices, dark mode support (TailwindCSS classes)
- [X] T080 [P] Implement code block syntax highlighting in html_formatter.py: detect language from codeBlock.language, add appropriate styling
- [X] T081 [P] Add navigation enhancements to HTML output in html_formatter.py: sticky table of contents, scroll-to-session links, back-to-top button
- [X] T082 [P] Create comprehensive end-to-end tests in tests/integration/test_e2e.py: full workflow from directory scan to file output
- [X] T083 [P] Update quickstart.md with real usage examples: installation, basic commands, troubleshooting common errors
- [X] T084 [P] Create CONTRIBUTING.md: development setup, running tests, code style guide
- [X] T085 Validate all CLI contract guarantees in tests/contract/test_cli_contract.py: exit codes, argument parsing, output formats, error messages
- [X] T086 Performance test in tests/integration/test_performance.py: verify 10-100 sessions parse in <5 seconds
- [X] T087 Cross-platform testing: validate on Linux, macOS, Windows (focus on path handling)
- [X] T088 Documentation review: ensure README, quickstart, CLI help text are consistent and complete

---

## Dependencies

**User Story Completion Order** (based on priorities):

```
Phase 1 (Setup) → Phase 2 (Foundation) → ┐
                                          ├→ Phase 3 (US1 - P1) 🎯 MVP
                                          ├→ Phase 4 (US2 - P2)
                                          ├→ Phase 5 (US4 - P2)
                                          └→ Phase 6 (US3 - P3)
                                          
All User Stories Complete → Phase 7 (Advanced Modes) → Phase 8 (Polish)
```

**Parallel Execution Opportunities:**

Within Phase 3 (US1):
- Tests T016-T022 can all be written in parallel
- Implementation T023-T026 (parser) parallel with T027-T034 (formatter)

Within Phase 4 (US2):
- Tests T039-T041 in parallel
- Implementation T042-T045 in parallel

Within Phase 5 (US4):
- Tests T049-T051 in parallel
- Implementation T052-T054 in parallel

Within Phase 6 (US3):
- Tests T060-T061 in parallel
- Implementation T062 parallel with T064-T066

Phase 8 (Polish) - most tasks T075-T084 can run in parallel

---

## Implementation Strategy

**MVP Definition**: Phase 3 (User Story 1) complete = Minimum Viable Product
- Parse WorkspaceStorage directory
- Extract chat messages (content, timestamp, role)
- Generate Copilot-style HTML output
- Basic error handling

**Incremental Delivery**:
1. Ship MVP (US1) first - provides immediate value
2. Add JSON export (US2) - enables automation use cases
3. Add error recovery (US4) - improves reliability
4. Add multi-workspace (US3) - handles edge cases
5. Add advanced modes - enhances flexibility
6. Polish and optimize - professional finish

**Testing Approach**: TDD (Test-Driven Development) per Constitution
- Write tests first (MUST fail initially)
- Implement feature to pass tests
- Refactor while keeping tests green

**Task Execution Notes**:
- Tasks marked [P] can be executed in parallel (no dependencies)
- Tasks without [P] have implicit dependencies on previous tasks in their phase
- Each phase checkpoint indicates deliverable is independently testable
- Follow checklist format strictly: `- [ ] T### [P?] [Story?] Description with file path`

---

## Task Count Summary

- **Total Tasks**: 88
- **Phase 1 (Setup)**: 10 tasks
- **Phase 2 (Foundation)**: 5 tasks
- **Phase 3 (US1 - P1)**: 23 tasks (7 tests + 16 implementation)
- **Phase 4 (US2 - P2)**: 10 tasks (3 tests + 7 implementation)
- **Phase 5 (US4 - P2)**: 11 tasks (3 tests + 8 implementation)
- **Phase 6 (US3 - P3)**: 9 tasks (2 tests + 7 implementation)
- **Phase 7 (Advanced)**: 7 tasks
- **Phase 8 (Polish)**: 14 tasks

**Parallelizable Tasks**: 52 tasks marked [P] (59%)

**MVP Task Count**: 38 tasks (Phases 1 + 2 + 3)

**Estimated Timeline**:
- MVP (Phases 1-3): 1-2 weeks
- Full Feature (All Phases): 3-4 weeks
- With parallel execution: 2-3 weeks for full feature

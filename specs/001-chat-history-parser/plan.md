# Implementation Plan: VS Code Chat History Parser

**Branch**: `001-chat-history-parser` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-chat-history-parser/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Parse VS Code WorkspaceStorage chat session files and extract conversation history into JSON and HTML formats. CLI tool accepts a WorkspaceStorage path, scans for chatSessions files (schema v3 with requests/response arrays), and outputs structured data or styled HTML with TailwindCSS. Supports multiple output modes (single file, per-session, per-workspace), concatenation, and graceful error handling for corrupted data.

## Technical Context

**Language/Version**: Python 3.12+ (modern Python features and performance)  
**Primary Dependencies**: Minimal standard library approach (json, pathlib, argparse); uv for package/environment management  
**Storage**: Read-only file system access to VS Code WorkspaceStorage (`~/.config/Code/User/workspaceStorage/` or platform equivalent)  
**Testing**: pytest with TDD approach (tests written before implementation per Constitution Principle IV)  
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)  
**Project Type**: Single-purpose CLI utility for parsing and formatting chat session data  
**Performance Goals**: Parse 10-100 chat sessions in <5 seconds (baseline); handle any number of sessions without warnings  
**Constraints**: Self-contained HTML output (TailwindCSS via CDN); graceful error handling for corrupted data; zero data loss on valid files; offline HTML viewing after generation  
**Scale/Scope**: Parse hundreds of chat session JSON files (typically 1-10KB each); extract 10-1000+ messages per session; generate HTML/JSON output <10MB typical case

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Single-Purpose Utility ✅

**Requirement**: Focus exclusively on parsing VS Code WorkspaceStorage chat session data.

**Compliance**: Feature spec clearly scoped to parsing chatSessions files and extracting conversation data. No chat manipulation, creation, or modification features. Clean boundary: read → parse → output.

**Status**: PASS

### Principle II: CLI-First Interface ✅

**Requirement**: All functionality accessible via command-line interface.

**Compliance**: 
- Input via required positional argument (WorkspaceStorage path)
- Output to stdout (JSON) or file (HTML)
- Errors to stderr with descriptive messages
- GNU-style flags for all options (-f/--format, -o/--output, -m/--html-mode, -c/--concatenate)
- Help (-h/--help) and version (-v/--version) flags
- No GUI components

**Status**: PASS

### Principle III: Format Flexibility ✅

**Requirement**: Support JSON and HTML output formats.

**Compliance**:
- JSON format for programmatic consumption (FR-004)
- HTML format with TailwindCSS styling (FR-005, FR-006)
- Format selection via -f/--format flag
- HTML output modes configurable (single/per-session/per-workspace)
- Self-contained HTML files viewable offline

**Status**: PASS

### Principle IV: Test-Driven Development ⚠️

**Requirement**: All parsing logic covered by tests before implementation.

**Compliance**: Spec includes comprehensive acceptance scenarios and edge cases. TDD must be enforced during implementation:
- Write tests first for each parsing function
- Test real chatSessions file samples
- Contract tests for JSON schema validation
- Integration tests for end-to-end workflows
- Edge case tests (corrupted files, special characters, empty directories)

**Status**: PASS (with implementation requirement to follow TDD process)

### Principle V: Graceful Error Handling ✅

**Requirement**: Handle errors without crashing or losing data.

**Compliance**:
- Path validation before parsing (FR-011)
- Graceful handling of malformed/corrupted files (FR-012)
- Specific error context to stderr (FR-009)
- Partial success support (parse valid data, report errors)
- Exit codes indicate success/failure (FR-010)
- Edge cases explicitly defined in spec

**Status**: PASS

### Technology Constraints ✅

**Requirement**: Python 3.12+, uv for package management, TailwindCSS via CDN, minimal dependencies.

**Compliance**:
- Python 3.12+ specified in Technical Context
- uv for environment/package management
- TailwindCSS loaded via CDN in HTML output (no build step)
- Standard library preferred (json, pathlib, argparse)
- No heavy frameworks or unnecessary dependencies

**Status**: PASS

### Overall Gate Status: **PASS** ✅

All constitutional principles satisfied. No violations or complexity justifications needed. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/chat_history_parser/
├── __init__.py           # Package initialization, version export
├── __main__.py           # Entry point for python -m chat_history_parser
├── cli.py                # Argument parsing, main() function
├── parser.py             # Core parsing logic for chatSessions files
├── models.py             # Data classes (ChatSession, Message, ParseResult)
├── scanner.py            # WorkspaceStorage directory scanning
├── formatters/
│   ├── __init__.py
│   ├── json_formatter.py  # JSON output formatting
│   └── html_formatter.py  # HTML generation with TailwindCSS
└── errors.py             # Custom exceptions and error handling

tests/
├── unit/                 # Unit tests for individual functions
│   ├── test_parser.py
│   ├── test_scanner.py
│   ├── test_models.py
│   └── test_formatters.py
├── integration/          # End-to-end workflow tests
│   ├── test_cli.py
│   └── test_full_parsing.py
├── contract/             # Schema validation tests
│   └── test_json_schema.py
└── fixtures/             # Sample chatSessions files for testing
    ├── valid_session.json
    ├── corrupted_session.json
    └── empty_session.json

pyproject.toml            # uv/project configuration
README.md                 # Installation and usage instructions
LICENSE                   # Project license
```

**Structure Decision**: Single project structure (Option 1) selected. This is a focused CLI tool with no frontend/backend separation or mobile components. Organized by function: parsing logic, data models, formatters (JSON/HTML), and CLI interface. Tests mirror source structure with unit/integration/contract separation per TDD principle.

## Complexity Tracking

No constitutional violations or complexity justifications needed. All principles satisfied by design.

---

## Constitution Check (Post-Phase 1 Design)

**Re-evaluation Date**: 2026-03-31  
**Artifacts Reviewed**: research.md, data-model.md, contracts/cli.md, quickstart.md

### Principle I: Single-Purpose Utility ✅

**Design Validation**:
- Data model defines 3 core entities (WorkspaceContext, ChatSession, Message) - all focused on parsing
- No entities for chat creation, modification, or user management
- CLI contract specifies read-only operations only
- Source structure separates parsing, formatting, and CLI layers cleanly

**Status**: PASS - Design maintains single-purpose scope

### Principle II: CLI-First Interface ✅

**Design Validation**:
- CLI contract documents complete POSIX-compliant interface
- All functionality accessible via command-line flags (5 optional flags defined)
- Standard streams properly defined (stdin unused, stdout for JSON, stderr for errors)
- Exit codes follow Unix conventions (0, 1, 2, 130)
- No GUI or web interface components in source structure

**Status**: PASS - CLI-first design verified

### Principle III: Format Flexibility ✅

**Design Validation**:
- Data model supports serialization to both JSON and HTML
- HTML generator module uses TailwindCSS via CDN (no build process)
- Three HTML output modes supported (single, per-session, per-workspace)
- CLI contract guarantees self-contained HTML files

**Status**: PASS - Format flexibility implemented

### Principle IV: Test-Driven Development ✅

**Design Validation**:
- Test structure defined with unit/integration/contract separation
- Quickstart guide specifies TDD workflow (write test → implement → refactor)
- Pytest fixtures planned for real chatSessions samples
- Test coverage for all parsing logic, CLI, and formatters

**Status**: PASS - TDD infrastructure ready

### Principle V: Graceful Error Handling ✅

**Design Validation**:
- Data model includes ParseError entity for error tracking
- Partial success strategy documented (continue on individual failures)
- CLI contract specifies error message format and stderr output
- Exit codes distinguish user errors (1) from data errors (2)
- Research.md includes defensive parsing patterns with fallbacks

**Status**: PASS - Error resilience built into design

### Technology Constraints ✅

**Design Validation**:
- Research.md confirms zero runtime dependencies beyond Python 3.12 stdlib
- Only development dependency: pytest
- TailwindCSS loaded via CDN (no Node.js or build tools)
- uv for package management (aligns with constitution)
- All technology choices documented in research.md with rationale

**Status**: PASS - Minimal dependency principle maintained

### Overall Post-Design Gate Status: **PASS** ✅

All constitutional principles verified in detailed design. No architecture drift or principle violations introduced during Phase 0-1. Design artifacts (data model, contracts, research) consistently implement constitutional requirements.

**Ready for Phase 2**: Implementation can proceed to `/speckit.tasks` for task generation.

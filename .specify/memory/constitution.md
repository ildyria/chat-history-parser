<!--
Sync Impact Report (2026-03-31):

Version change: 1.0.0 → 1.1.0

Amendment: Added HTML output format with TailwindCSS and uv package manager.

Modified principles:
- Principle III (Format Flexibility): Added HTML output format requirement with TailwindCSS
- Technology Constraints: Added uv as package manager and TailwindCSS for HTML styling

Added sections: N/A
Removed sections: N/A

Rationale: HTML output provides superior readability for human consumption with
rich formatting, navigation, and styling. TailwindCSS enables rapid, consistent
styling without custom CSS. uv provides fast, reliable Python package management.

Template consistency review:
✅ spec-template.md - Aligned (no changes required)
✅ plan-template.md - Constitution Check section ready
✅ tasks-template.md - Task categorization aligned with principles
✅ commands/*.md - No agent-specific references to update

Follow-up TODOs: 
- Update any existing specs to reference HTML output format
- Ensure plan templates validate HTML generation requirements
-->

# Chat History Parser Constitution

## Core Principles

### I. Single-Purpose Utility

This project MUST focus exclusively on parsing VS Code WorkspaceStorage chat session data.

- Parse chatSessions files from VS Code WorkspaceStorage directories
- Extract conversation history and metadata from storage structures
- No feature creep: reject additions unrelated to parsing chat history
- Clear boundary: parsing and extraction only, not chat manipulation or creation

**Rationale**: Single-purpose tools are easier to test, maintain, and reason about.
Users need reliable parsing; expanding scope risks quality and maintainability.

### II. CLI-First Interface

All functionality MUST be accessible via command-line interface.

- Input: WorkspaceStorage path via command-line argument
- Output: Parsed chat data to stdout (structured format)
- Errors: stderr with descriptive messages and non-zero exit codes
- No GUI required; CLI enables scripting and automation

**Rationale**: CLI tools integrate into workflows, scripts, and pipelines. They are
platform-agnostic and don't require display servers or windowing systems.

### III. Format Flexibility

The parser MUST support multiple output formats.

- JSON format for programmatic consumption (required)
- Human-readable HTML format for manual inspection (required)
- Plain text format for simple/legacy workflows (optional)
- Format selection via command-line flag
- Well-documented schema for each output format
- HTML output MUST use TailwindCSS for styling and readability

**Rationale**: Different use cases demand different formats. Developers need JSON
for automation; humans need rich HTML formatting for easy reading and navigation.
TailwindCSS provides consistent, professional styling without custom CSS overhead.

### IV. Test-Driven Development

All parsing logic MUST be covered by tests before implementation.

- Write tests first: define expected behavior through test cases
- Red-Green-Refactor: tests fail → implement → tests pass → refactor
- Test real VS Code WorkspaceStorage samples and edge cases
- Contract tests for output format stability
- Integration tests for end-to-end parsing workflows

**Rationale**: Parsing is error-prone. TDD ensures correctness and prevents
regressions. Tests document expected behavior and serve as living specifications.

### V. Graceful Error Handling

The parser MUST handle errors without crashing or losing data.

- Validate WorkspaceStorage path before parsing
- Handle missing, malformed, or corrupted chatSessions files gracefully
- Report specific error context (which file, what failed, why)
- Partial success: parse what's valid, report what's broken
- No silent failures: always communicate status to user

**Rationale**: Real-world data is messy. Users need actionable error messages,
not stack traces. Graceful degradation ensures usability even with corrupt data.
+ (for broad compatibility and ease of JSON handling)

**Package Manager**: uv (for fast, reliable dependency management and virtual environments)

**Core Dependencies**:

- Standard library preferentially for portability
- Minimal external dependencies to reduce installation friction
- JSON parsing via built-in `json` module
- File system operations via `pathlib`
- TailwindCSS via CDN for HTML styling (no build step required)

**HTML Generation**:

- Use Python templating or direct HTML generation
- TailwindCSS loaded from CDN in generated HTML files
- No JavaScript build tools (webpack, vite, etc.)
- Self-contained HTML files that work offline after generation

**Prohibited Dependencies**:

- No heavy frameworks (Django, Flask, etc.) for a CLI tool
- Avoid dependencies requiring compilation unless absolutely necessary
- No platform-specific dependencies without clear justification
- No NodeJS-based build processes for a Python CLI tool

**Rationale**: Keep the tool lightweight, portable, and easy to install.
uv provides fast dependency resolution and environment management. TailwindCSS
via CDN eliminates build complexity while providing professional stylingear justification

**Rationale**: Keep the tool lightweight, portable, and easy to install.
Minimize dependency hell and version conflicts.

## Development Workflow

**Branching Strategy**:

- No branches needed. All development occurs directly on main with strict adherence to principles.
- All work must reference a spec.md and tasks.md
- Main branch always stable and tested

**Code Quality Gates**:

- All tests pass before merge (enforced)
- Linting passes (ruff or equivalent)
- Type hints for all public functions (mypy validation)
- Documentation strings for all modules and public functions

**Review Process**:

- Self-review against this constitution before committing
- Verify test coverage includes new code paths
- Confirm output format backward compatibility

## Governance

This constitution supersedes all other development practices and preferences.

**Amendment Process**:

- Amendments require explicit version bump (MAJOR for breaking principle changes,
  MINOR for new principles, PATCH for clarifications)
- Document rationale for all amendments in Sync Impact Report
- Update all dependent templates and documentation artifacts
- Constitution changes must be reviewed for impact on active features

**Compliance**:

- Every feature specification must reference relevant principles
- Every implementation plan must include Constitution Check gate
- Complexity or principle violations must be explicitly justified in plan.md
- Use this constitution file for alignment during all speckit workflows

**Version**: 1.0.0 | **Ratified**: 2026-03-31 | **Last Amended**: 2026-03-31

"""Data models for chat sessions, messages, and workspace context."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class WorkspaceContext:
    """Represents a VS Code workspace directory containing chat session data.
    
    Attributes:
        workspace_id: 32-character hex identifier from directory name
        base_path: Absolute path to workspaceStorage directory
        session_files: List of chatSessions JSON file paths
        workspace_name: Human-readable workspace name extracted from workspace.json
    """
    workspace_id: str
    base_path: Path
    session_files: list[Path] = field(default_factory=list)
    workspace_name: str | None = None
    
    def __post_init__(self):
        """Validate workspace context after initialization."""
        if not self.base_path.exists():
            raise ValueError(f"Workspace path does not exist: {self.base_path}")
        if not self.base_path.is_dir():
            raise ValueError(f"Workspace path is not a directory: {self.base_path}")


@dataclass
class Message:
    """Individual message in a chat conversation with minimal metadata.
    
    Per clarification (2026-03-31): Only three fields are extracted:
    - content: Message text
    - timestamp: When message was sent
    - role: 'user' or 'assistant'
    
    Attributes:
        content: Message text content
        timestamp: When message was sent
        role: Speaker role ('user' or 'assistant')
    """
    content: str
    timestamp: datetime
    role: str
    
    def __post_init__(self):
        """Validate message after initialization."""
        if not self.content or not self.content.strip():
            raise ValueError("Message content cannot be empty")
        if self.role not in ('user', 'assistant'):
            raise ValueError(f"Invalid role: {self.role}. Must be 'user' or 'assistant'")


@dataclass
class ChatSession:
    """Represents a single chat conversation from a chatSessions JSON file.

    Source: chatSessions JSON schema v3 with requests/response arrays

    Attributes:
        session_id: Unique identifier from JSON sessionId field
        creation_date: Session creation timestamp (optional)
        source_file: Path to source JSON file
        messages: Ordered list of conversation messages
        parse_errors: List of parsing error descriptions
        workspace_id: Optional workspace identifier for multi-workspace scenarios
        requester_username: Display name of the user who sent messages
        responder_username: Display name of the assistant/responder
        requester_avatar_url: Reconstructed URL for the requester's avatar image
        responder_avatar_url: Reconstructed URL for the responder's avatar image
    """
    session_id: str
    source_file: Path
    messages: list[Message] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)
    creation_date: datetime | None = None
    workspace_id: str | None = None
    requester_username: str | None = None
    responder_username: str | None = None
    requester_avatar_url: str | None = None
    responder_avatar_url: str | None = None
    responder_avatar_icon_id: str | None = None
    
    def __post_init__(self):
        """Validate chat session after initialization."""
        if not self.session_id or not self.session_id.strip():
            raise ValueError("Session ID cannot be empty")
        if not self.source_file.exists():
            raise ValueError(f"Source file does not exist: {self.source_file}")


@dataclass
class ParseError:
    """Represents a parsing error encountered during chat session extraction.
    
    Attributes:
        file_path: Path to the file that caused the error
        error_type: Type of error (e.g., 'JSONDecodeError', 'MissingField')
        message: Descriptive error message
        timestamp: When the error occurred
    """
    file_path: str
    error_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FormatterContext:
    """Context for formatters containing parsed sessions and metadata.
    
    This is separate from WorkspaceContext (used by scanner) and is specifically
    for passing data to formatters for output generation.
    
    Attributes:
        workspace_path: String path to workspace (for display)
        sessions: List of parsed ChatSession objects
        parse_errors: List of errors encountered during parsing
    """
    workspace_path: str
    sessions: list['ChatSession'] = field(default_factory=list)
    parse_errors: list[ParseError] = field(default_factory=list)

"""Custom exception classes for error handling."""


class ChatHistoryParserError(Exception):
    """Base exception for all chat history parser errors."""
    pass


class WorkspaceNotFoundError(ChatHistoryParserError):
    """Raised when the specified WorkspaceStorage path does not exist or is invalid."""
    
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"WorkspaceStorage path not found or invalid: {path}")


class InvalidSessionFileError(ChatHistoryParserError):
    """Raised when a chatSessions file cannot be read or parsed."""
    
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Invalid session file '{file_path}': {reason}")


class ParsingError(ChatHistoryParserError):
    """Raised when parsing fails for a specific chat session or message."""
    
    def __init__(self, context: str, reason: str):
        self.context = context
        self.reason = reason
        super().__init__(f"Parsing error in {context}: {reason}")

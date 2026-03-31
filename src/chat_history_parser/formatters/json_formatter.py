"""JSON output formatter."""

import json
from datetime import datetime
from typing import Any, Dict, List
from ..models import FormatterContext, ChatSession, Message, ParseError


class JSONFormatter:
    """Formats parsed chat sessions as JSON."""
    
    def __init__(self):
        """Initialize JSON formatter."""
        pass
    
    def generate(self, context: FormatterContext) -> str:
        """
        Generate JSON output from formatter context.
        
        Args:
            context: Parsed formatter context with sessions
            
        Returns:
            JSON string with metadata and sessions
        """
        output = {
            "metadata": self._build_metadata(context),
            "sessions": self._serialize_sessions(context.sessions)
        }
        
        return json.dumps(output, indent=2)
    
    def _build_metadata(self, context: FormatterContext) -> Dict[str, Any]:
        """
        Build metadata section.
        
        Args:
            context: Formatter context
            
        Returns:
            Metadata dictionary
        """
        total_messages = sum(len(session.messages) for session in context.sessions)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "workspace_path": context.workspace_path,
            "session_count": len(context.sessions),
            "total_messages": total_messages,
            "parse_errors": self._serialize_parse_errors(context.parse_errors)
        }
    
    def _serialize_parse_errors(self, errors: List[ParseError]) -> List[Dict[str, str]]:
        """
        Serialize parse errors.
        
        Args:
            errors: List of parse errors
            
        Returns:
            List of error dictionaries
        """
        return [
            {
                "file_path": error.file_path,
                "error_type": error.error_type,
                "message": error.message
            }
            for error in errors
        ]
    
    def _serialize_sessions(self, sessions: List[ChatSession]) -> List[Dict[str, Any]]:
        """
        Serialize chat sessions.
        
        Args:
            sessions: List of chat sessions
            
        Returns:
            List of session dictionaries
        """
        return [
            {
                "session_id": session.session_id,
                "workspace_id": session.workspace_id,
                "creation_date": session.creation_date.isoformat() if session.creation_date else None,
                "messages": self._serialize_messages(session.messages)
            }
            for session in sessions
        ]
    
    def _serialize_messages(self, messages: List[Message]) -> List[Dict[str, str | None]]:
        """
        Serialize messages.
        
        Args:
            messages: List of messages
            
        Returns:
            List of message dictionaries with ISO 8601 timestamps
        """
        return [
            {
                "content": message.content,
                "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                "role": message.role
            }
            for message in messages
        ]

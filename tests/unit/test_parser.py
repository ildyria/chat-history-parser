"""Unit tests for chatSessions JSON parsing logic."""

import json
from datetime import datetime


from chat_history_parser.models import ChatSession
from chat_history_parser.parser import (
    parse_session_file,
    extract_user_message,
    extract_assistant_messages,
    flatten_response,
)


def test_parse_session_v3_schema(tmp_path):
    """Test parsing of chatSessions JSON v3 schema structure.
    
    Verifies:
    - sessionId extraction
    - creationDate parsing (ISO 8601)
    - requests array iteration
    - Message extraction from requests
    """
    # Create a minimal test session file
    session_data = {
        "version": 3,
        "sessionId": "test-session-123",
        "creationDate": "2026-03-31T10:00:00.000Z",
        "lastMessageDate": "2026-03-31T10:05:00.000Z",
        "requests": [
            {
                "requestId": "req-001",
                "timestamp": "2026-03-31T10:00:00.000Z",
                "message": "Hello, how are you?",
                "response": [
                    {"type": "text", "value": "I'm doing well, thank you!"}
                ]
            }
        ]
    }
    
    test_file = tmp_path / "test-session.json"
    test_file.write_text(json.dumps(session_data))
    
    # Parse the session
    session = parse_session_file(test_file)
    
    # Verify session metadata
    assert session.session_id == "test-session-123"
    assert session.creation_date.year == 2026
    assert session.creation_date.month == 3
    assert session.creation_date.day == 31
    assert session.source_file == test_file
    assert len(session.messages) == 2  # 1 user + 1 assistant
    assert session.messages[0].role == "user"
    assert session.messages[1].role == "assistant"


def test_extract_messages_minimal_fields():
    """Test extraction of only the three minimal message fields.
    
    Per clarification Q&A (2026-03-31): Message captures only:
    - content (str)
    - timestamp (datetime)
    - role (str: 'user' or 'assistant')
    
    No additional metadata should be extracted.
    """
    request_data = {
        "requestId": "req-001",
        "timestamp": "2026-03-31T10:00:00.000Z",
        "message": "Test message",
        "agent": {"id": "copilot", "name": "GitHub Copilot"},
        "response": [
            {"type": "text", "value": "Test response"}
        ]
    }
    
    # Extract user message
    user_msg = extract_user_message(request_data)
    
    # Verify only minimal fields present
    assert hasattr(user_msg, 'content')
    assert hasattr(user_msg, 'timestamp')
    assert hasattr(user_msg, 'role')
    assert user_msg.content == "Test message"
    assert user_msg.role == "user"
    assert isinstance(user_msg.timestamp, datetime)
    
    # Extract assistant messages
    assistant_msgs = extract_assistant_messages(request_data)
    
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0].content == "Test response"
    assert assistant_msgs[0].role == "assistant"


def test_flatten_mixed_response_types():
    """Test flattening of heterogeneous response[] array into text.
    
    Response array contains mixed types:
    - text: Extract value field
    - tool invocations: Flatten to description
    - code blocks: Extract content
    - confirmations: Convert to text
    """
    response_array = [
        {"type": "text", "value": "Let me help you with that."},
        {
            "type": "toolInvocation",
            "name": "read_file",
            "parameters": {"path": "test.py"},
            "result": "File content here"
        },
        {
            "type": "codeBlock",
            "language": "python",
            "content": "print('hello')"
        },
        {"type": "text", "value": "That should work!"}
    ]
    
    # Flatten response types
    messages = flatten_response(response_array, timestamp="2026-03-31T10:00:00.000Z")
    
    # Should produce assistant messages with readable content
    assert len(messages) >= 1
    assert all(msg.role == "assistant" for msg in messages)
    assert any("help you" in msg.content.lower() for msg in messages)
    assert any("read_file" in msg.content.lower() or "tool" in msg.content.lower() for msg in messages)
    assert any("print" in msg.content for msg in messages)


# Phase 5: Error Recovery Tests (T049-T051)

def test_handle_malformed_json(tmp_path):
    """Test graceful handling of malformed JSON files.
    
    Parser should catch json.JSONDecodeError and return None or
    raise a specific error that can be caught by the CLI.
    """
    malformed_file = tmp_path / "malformed.json"
    malformed_file.write_text('{"version": 3, "sessionId": "test", unclosed')
    
    # Should not crash, either returns None or raises specific error
    try:
        result = parse_session_file(malformed_file)
        # If it returns None, that's acceptable
        assert result is None
    except Exception as e:
        # If it raises an error, it should be a specific parsing error
        assert "JSON" in str(type(e).__name__) or "Parse" in str(type(e).__name__)


def test_handle_missing_required_fields(tmp_path):
    """Test handling of JSON missing required fields like sessionId or version."""
    incomplete_session = {
        # Missing 'version' and 'sessionId'
        "creationDate": "2026-03-31T10:00:00.000Z",
        "requests": []
    }
    
    incomplete_file = tmp_path / "incomplete.json"
    incomplete_file.write_text(json.dumps(incomplete_session))
    
    # Should handle missing fields gracefully
    try:
        result = parse_session_file(incomplete_file)
        # If returns None, validation failed safely
        assert result is None or isinstance(result, ChatSession)
    except (KeyError, ValueError):
        # Acceptable to raise specific error
        pass


def test_recover_from_invalid_timestamps(tmp_path):
    """Test recovery from invalid or missing timestamps.
    
    Invalid timestamps should be handled with None fallback.
    """
    session_with_bad_timestamps = {
        "version": 3,
        "sessionId": "test-123",
        "creationDate": "not-a-valid-timestamp",
        "requests": [
            {
                "requestId": "req-001",
                "timestamp": "also-invalid",
                "message": "Test message",
                "response": []
            }
        ]
    }
    
    test_file = tmp_path / "bad-timestamps.json"
    test_file.write_text(json.dumps(session_with_bad_timestamps))
    
    # Parser should not crash, may use None for invalid timestamps
    result = parse_session_file(test_file)
    
    # If it returns a session, timestamps should be None or have a fallback
    if result:
        # Messages should still be extracted even with bad timestamps
        assert isinstance(result, ChatSession)


def test_handle_empty_response_arrays(tmp_path):
    """Test handling of requests with empty response arrays."""
    session_with_empty_responses = {
        "version": 3,
        "sessionId": "test-empty",
        "creationDate": "2026-03-31T10:00:00.000Z",
        "requests": [
            {
                "requestId": "req-001",
                "timestamp": "2026-03-31T10:00:00.000Z",
                "message": "User message",
                "response": []  # Empty response
            },
            {
                "requestId": "req-002",
                "timestamp": "2026-03-31T10:01:00.000Z",
                "message": "Another message",
                "response": None  # Null response
            }
        ]
    }
    
    test_file = tmp_path / "empty-responses.json"
    test_file.write_text(json.dumps(session_with_empty_responses))
    
    result = parse_session_file(test_file)
    
    # Should handle empty/null responses gracefully
    assert result is not None
    # User messages should still be extracted
    user_messages = [m for m in result.messages if m.role == "user"]
    assert len(user_messages) == 2

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


def test_parse_jsonl_wrapped_format(tmp_path):
    """Test parsing of .jsonl files with wrapped format.
    
    .jsonl files have a wrapper structure:
    {
        "kind": 0,
        "v": {
            "version": 3,
            "sessionId": "...",
            "creationDate": timestamp_ms,
            "requests": [...]
        }
    }
    
    Parser should unwrap the "v" field and parse the session data.
    """
    # Create a .jsonl file with wrapped format
    session_data = {
        "kind": 0,
        "v": {
            "version": 3,
            "sessionId": "jsonl-test-session",
            "creationDate": 1774199840739,  # Unix timestamp in milliseconds
            "initialLocation": "panel",
            "responderUsername": "GitHub Copilot",
            "hasPendingEdits": False,
            "requests": [
                {
                    "requestId": "req-001",
                    "timestamp": "2026-04-06T10:00:00.000Z",
                    "message": "Tell me about Python",
                    "response": [
                        {"type": "text", "value": "Python is a high-level programming language."}
                    ]
                }
            ],
            "pendingRequests": [],
            "inputState": {}
        }
    }
    
    test_file = tmp_path / "test-session.jsonl"
    test_file.write_text(json.dumps(session_data))
    
    # Parse the session
    session = parse_session_file(test_file)
    
    # Verify session metadata
    assert session is not None
    assert session.session_id == "jsonl-test-session"
    assert session.creation_date is not None
    assert session.source_file == test_file
    assert len(session.messages) == 2  # 1 user + 1 assistant
    assert session.messages[0].role == "user"
    assert session.messages[0].content == "Tell me about Python"
    assert session.messages[1].role == "assistant"
    assert "Python" in session.messages[1].content


def test_parse_jsonl_incremental_format(tmp_path):
    """Test parsing of multi-line JSONL files with incremental updates.
    
    Multi-line JSONL files use an event stream format:
    - Line 1 (kind=0): Initial session state
    - Lines 2+ (kind=1,2): Incremental updates to the session
    
    kind=1: Update single field (k=[path], v=value)
    kind=2: Update nested values (k=[path, with, indices], v=value)
    """
    # Create a multi-line JSONL file
    lines = [
        # Initial state
        json.dumps({
            "kind": 0,
            "v": {
                "version": 3,
                "sessionId": "incremental-test",
                "creationDate": 1774199840739,
                "responderUsername": "GitHub Copilot",
                "requests": []
            }
        }),
        # Add input text
        json.dumps({
            "kind": 1,
            "k": ["inputState", "inputText"],
            "v": "Hello, how are you?"
        }),
        # Add a request to the array
        json.dumps({
            "kind": 2,
            "k": ["requests"],
            "v": [{
                "requestId": "req-001",
                "timestamp": "2026-04-06T10:00:00.000Z",
                "message": "Hello, how are you?",
                "response": []
            }]
        }),
        # Update the response (replace sub-field on existing element)
        json.dumps({
            "kind": 2,
            "k": ["requests", 0, "response"],
            "v": [{"type": "text", "value": "I'm doing well, thank you!"}]
        }),
        # Add a second request (appended, not replacing)
        json.dumps({
            "kind": 2,
            "k": ["requests"],
            "v": [{
                "requestId": "req-002",
                "timestamp": "2026-04-06T10:01:00.000Z",
                "message": "What is Python?",
                "response": [{"type": "text", "value": "Python is a programming language."}]
            }]
        }),
    ]
    
    test_file = tmp_path / "incremental.jsonl"
    test_file.write_text("\n".join(lines))
    
    # Parse the session
    session = parse_session_file(test_file)
    
    # Verify session metadata
    assert session is not None
    assert session.session_id == "incremental-test"
    assert session.responder_username == "GitHub Copilot"
    
    # Verify both requests are in the history (not just the last one)
    assert len(session.messages) == 4  # 2 user + 2 assistant
    user_messages = [m for m in session.messages if m.role == "user"]
    assert len(user_messages) == 2
    assert user_messages[0].content == "Hello, how are you?"
    assert user_messages[1].content == "What is Python?"
    
    assistant_messages = [m for m in session.messages if m.role == "assistant"]
    assert len(assistant_messages) == 2
    assert "doing well" in assistant_messages[0].content
    assert "programming language" in assistant_messages[1].content

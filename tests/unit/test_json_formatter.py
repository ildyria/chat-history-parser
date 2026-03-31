"""Unit tests for JSONFormatter."""

import json
from datetime import datetime
from pathlib import Path
from chat_history_parser.models import ChatSession, Message, FormatterContext, ParseError
from chat_history_parser.formatters.json_formatter import JSONFormatter


def test_generate_json_output():
    """Test that JSONFormatter generates valid JSON output."""
    # Setup test data
    messages = [
        Message(content="Hello", timestamp=datetime(2026, 1, 1, 10, 0, 0), role="user"),
        Message(content="Hi there!", timestamp=datetime(2026, 1, 1, 10, 0, 5), role="assistant"),
    ]
    
    session = ChatSession(
        session_id="test123",
        source_file=Path("/tmp/test.json"),
        creation_date=datetime(2026, 1, 1, 10, 0, 0),
        messages=messages,
        workspace_id=None,
        parse_errors=[]
    )
    
    context = FormatterContext(
        workspace_path="/path/to/workspace",
        sessions=[session]
    )
    
    # Generate JSON
    formatter = JSONFormatter()
    output = formatter.generate(context)
    
    # Validate it's valid JSON
    data = json.loads(output)
    
    # Check structure
    assert "metadata" in data
    assert "sessions" in data
    
    # Check metadata
    assert data["metadata"]["workspace_path"] == "/path/to/workspace"
    assert data["metadata"]["session_count"] == 1
    assert data["metadata"]["total_messages"] == 2
    assert "generated_at" in data["metadata"]
    
    # Check sessions
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["session_id"] == "test123"
    assert len(data["sessions"][0]["messages"]) == 2
    
    # Check messages
    msg1 = data["sessions"][0]["messages"][0]
    assert msg1["content"] == "Hello"
    assert msg1["role"] == "user"
    assert "timestamp" in msg1
    
    msg2 = data["sessions"][0]["messages"][1]
    assert msg2["content"] == "Hi there!"
    assert msg2["role"] == "assistant"


def test_generate_with_parse_errors():
    """Test that parse errors are included in JSON output."""
    error = ParseError(
        file_path="/path/to/bad.json",
        error_type="JSONDecodeError",
        message="Invalid JSON"
    )
    
    context = FormatterContext(
        workspace_path="/path/to/workspace",
        sessions=[],
        parse_errors=[error]
    )
    
    formatter = JSONFormatter()
    output = formatter.generate(context)
    data = json.loads(output)
    
    assert "parse_errors" in data["metadata"]
    assert len(data["metadata"]["parse_errors"]) == 1
    assert data["metadata"]["parse_errors"][0]["file_path"] == "/path/to/bad.json"
    assert data["metadata"]["parse_errors"][0]["error_type"] == "JSONDecodeError"


def test_generate_empty_workspace():
    """Test JSON output for workspace with no sessions."""
    context = FormatterContext(
        workspace_path="/empty",
        sessions=[]
    )
    
    formatter = JSONFormatter()
    output = formatter.generate(context)
    data = json.loads(output)
    
    assert data["metadata"]["session_count"] == 0
    assert data["metadata"]["total_messages"] == 0
    assert data["sessions"] == []


def test_iso8601_timestamps():
    """Test that timestamps are serialized as ISO 8601."""
    messages = [
        Message(
            content="Test",
            timestamp=datetime(2026, 3, 31, 14, 30, 45),
            role="user"
        )
    ]
    
    session = ChatSession(
        session_id="test",
        source_file=Path("/tmp/test.json"),
        creation_date=datetime(2026, 3, 31, 14, 30, 0),
        messages=messages
    )
    
    context = FormatterContext(
        workspace_path="/test",
        sessions=[session]
    )
    
    formatter = JSONFormatter()
    output = formatter.generate(context)
    data = json.loads(output)
    
    # Check ISO 8601 format
    msg_timestamp = data["sessions"][0]["messages"][0]["timestamp"]
    assert "2026-03-31" in msg_timestamp
    assert "14:30:45" in msg_timestamp
    
    session_date = data["sessions"][0]["creation_date"]
    assert "2026-03-31" in session_date
    assert "14:30:00" in session_date

"""Contract tests for JSON output schema."""

import json
from datetime import datetime
from pathlib import Path
from chat_history_parser.models import ChatSession, Message, FormatterContext, ParseError
from chat_history_parser.formatters.json_formatter import JSONFormatter


def test_json_schema_compliance():
    """Test that JSON output complies with the documented schema."""
    # Create test data
    messages = [
        Message(content="User message", timestamp=datetime(2026, 1, 1, 10, 0, 0), role="user"),
        Message(content="Assistant response", timestamp=datetime(2026, 1, 1, 10, 0, 5), role="assistant"),
    ]
    
    session = ChatSession(
        session_id="abc123",
        source_file=Path("/tmp/test.json"),
        creation_date=datetime(2026, 1, 1, 10, 0, 0),
        messages=messages
    )
    
    error = ParseError(
        file_path="/path/error.json",
        error_type="JSONDecodeError",
        message="Test error"
    )
    
    context = FormatterContext(
        workspace_path="/workspace",
        sessions=[session],
        parse_errors=[error]
    )
    
    # Generate output
    formatter = JSONFormatter()
    output = formatter.generate(context)
    data = json.loads(output)
    
    # Validate root structure
    assert isinstance(data, dict), "Root must be an object"
    assert set(data.keys()) == {"metadata", "sessions"}, "Root must have exactly metadata and sessions"
    
    # Validate metadata structure
    metadata = data["metadata"]
    assert isinstance(metadata, dict)
    required_metadata_fields = {"generated_at", "workspace_path", "session_count", "total_messages", "parse_errors"}
    assert set(metadata.keys()) == required_metadata_fields
    
    assert isinstance(metadata["generated_at"], str)
    assert isinstance(metadata["workspace_path"], str)
    assert isinstance(metadata["session_count"], int)
    assert isinstance(metadata["total_messages"], int)
    assert isinstance(metadata["parse_errors"], list)
    
    # Validate parse_errors structure
    assert len(metadata["parse_errors"]) == 1
    error_obj = metadata["parse_errors"][0]
    assert set(error_obj.keys()) == {"file_path", "error_type", "message"}
    assert isinstance(error_obj["file_path"], str)
    assert isinstance(error_obj["error_type"], str)
    assert isinstance(error_obj["message"], str)
    
    # Validate sessions structure
    sessions = data["sessions"]
    assert isinstance(sessions, list)
    assert len(sessions) == 1
    
    session_obj = sessions[0]
    required_session_fields = {"session_id", "workspace_id", "creation_date", "messages"}
    assert set(session_obj.keys()) == required_session_fields
    
    assert isinstance(session_obj["session_id"], str)
    assert isinstance(session_obj["creation_date"], str) or session_obj["creation_date"] is None
    assert session_obj["workspace_id"] is None or isinstance(session_obj["workspace_id"], str)
    assert isinstance(session_obj["messages"], list)
    
    # Validate messages structure
    messages_list = session_obj["messages"]
    assert len(messages_list) == 2
    
    for msg in messages_list:
        required_message_fields = {"content", "timestamp", "role"}
        assert set(msg.keys()) == required_message_fields
        assert isinstance(msg["content"], str)
        assert isinstance(msg["timestamp"], str)
        assert isinstance(msg["role"], str)
        assert msg["role"] in ["user", "assistant"]


def test_json_schema_minimal():
    """Test schema compliance with minimal data (no errors, no sessions)."""
    context = FormatterContext(
        workspace_path="/empty",
        sessions=[]
    )
    
    formatter = JSONFormatter()
    output = formatter.generate(context)
    data = json.loads(output)
    
    # Validate structure
    assert "metadata" in data
    assert "sessions" in data
    
    # Empty parse_errors should still be present
    assert data["metadata"]["parse_errors"] == []
    assert data["sessions"] == []
    assert data["metadata"]["session_count"] == 0
    assert data["metadata"]["total_messages"] == 0


def test_json_valid_parseable():
    """Test that output is valid, parseable JSON (can round-trip)."""
    messages = [Message(content="Test", timestamp=datetime.now(), role="user")]
    session = ChatSession(
        session_id="test",
        source_file=Path("/tmp/test.json"),
        creation_date=datetime.now(),
        messages=messages
    )
    context = FormatterContext(workspace_path="/test", sessions=[session])
    
    formatter = JSONFormatter()
    output = formatter.generate(context)
    
    # Parse it
    data = json.loads(output)
    
    # Re-serialize and parse again (round-trip)
    output2 = json.dumps(data)
    data2 = json.loads(output2)
    
    # Should be identical
    assert data == data2

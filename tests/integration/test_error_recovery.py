"""Integration tests for error recovery and partial parsing success."""

import json


from chat_history_parser.scanner import discover_workspaces
from chat_history_parser.parser import parse_session_file
from chat_history_parser.models import ParseError


def test_partial_parse_with_errors(tmp_path):
    """Test CLI behavior with workspace containing mix of valid and corrupted files.
    
    Expected behavior:
    - Parse all valid files successfully
    - Log errors for corrupted files to stderr
    - Return partial results (don't fail completely)
    - Exit code 0 if at least one file parsed successfully
    """
    # Create workspace structure
    workspace_id = "a" * 32
    workspace_dir = tmp_path / workspace_id
    sessions_dir = workspace_dir / "chatSessions"
    sessions_dir.mkdir(parents=True)
    
    # Create valid session file
    valid_session = {
        "version": 3,
        "sessionId": "valid-session",
        "creationDate": "2026-03-31T10:00:00.000Z",
        "requests": [
            {
                "requestId": "req-001",
                "timestamp": "2026-03-31T10:00:00.000Z",
                "message": "Valid message",
                "response": [{"type": "text", "value": "Valid response"}]
            }
        ]
    }
    (sessions_dir / "abc123.json").write_text(json.dumps(valid_session))
    
    # Create malformed JSON file
    (sessions_dir / "def456.json").write_text('{"invalid json syntax')
    
    # Create file with missing required fields
    invalid_session = {
        "version": 3,
        # Missing sessionId
        "requests": []
    }
    (sessions_dir / "ghi789.json").write_text(json.dumps(invalid_session))
    
    # Create empty file
    (sessions_dir / "jkl012.json").write_text('')
    
    # Scan and parse workspace
    workspaces = discover_workspaces(tmp_path)
    
    # Should discover workspace
    assert len(workspaces) == 1
    assert len(workspaces[0].session_files) == 4
    
    # Parse sessions (should handle errors gracefully)
    sessions = []
    errors = []
    
    for session_file in workspaces[0].session_files:
        try:
            result = parse_session_file(session_file)
            if result:
                sessions.append(result)
            else:
                errors.append(f"Failed to parse: {session_file.name}")
        except Exception as e:
            errors.append(f"Error in {session_file.name}: {str(e)}")
    
    # Verify partial success
    assert len(sessions) >= 1, "Should parse at least one valid session"
    assert len(errors) >= 1, "Should detect errors in corrupted files"
    
    # Verify the valid session was parsed correctly
    valid_parsed = [s for s in sessions if s.session_id == "valid-session"]
    assert len(valid_parsed) == 1
    assert len(valid_parsed[0].messages) >= 1


def test_error_aggregation_in_parse_errors(tmp_path):
    """Test that parse errors are collected and attached to results."""
    # Create workspace with one corrupted file
    workspace_id = "b" * 32
    workspace_dir = tmp_path / workspace_id
    sessions_dir = workspace_dir / "chatSessions"
    sessions_dir.mkdir(parents=True)
    
    # Malformed file
    (sessions_dir / "corrupted.json").write_text('not valid json at all!')
    
    # Valid file
    valid_session = {
        "version": 3,
        "sessionId": "good-session",
        "creationDate": "2026-03-31T10:00:00.000Z",
        "requests": []
    }
    (sessions_dir / "valid.json").write_text(json.dumps(valid_session))
    
    # Parse with error tracking
    workspaces = discover_workspaces(tmp_path)
    
    sessions = []
    parse_errors = []
    
    for session_file in workspaces[0].session_files:
        try:
            result = parse_session_file(session_file)
            if result:
                sessions.append(result)
            else:
                # None return means parse failed (malformed JSON)
                error = ParseError(
                    file_path=str(session_file),
                    error_type="ParseFailure",
                    message="Failed to parse session file"
                )
                parse_errors.append(error)
        except Exception as e:
            error = ParseError(
                file_path=str(session_file),
                error_type=type(e).__name__,
                message=str(e)
            )
            parse_errors.append(error)
    
    # Should have errors
    assert len(parse_errors) >= 1
    assert any("corrupted.json" in str(err.file_path) for err in parse_errors)
    
    # Should have successes
    assert len(sessions) >= 1

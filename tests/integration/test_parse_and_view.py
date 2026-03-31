"""Integration tests for parsing workspace and generating HTML output."""

import json


from chat_history_parser.scanner import discover_workspaces
from chat_history_parser.parser import parse_session_file
from chat_history_parser.formatters.html_formatter import HTMLFormatter


def test_parse_workspace_generate_html(tmp_path):
    """End-to-end test: scan workspace, parse sessions, generate HTML.
    
    This test verifies the complete workflow:
    1. Discover workspace with chatSessions files
    2. Parse each session file
    3. Generate unified HTML output
    4. Verify HTML contains all conversation data
    """
    # Create test workspace structure
    workspace_id = "a" * 32  # 32-character hex
    workspace_dir = tmp_path / workspace_id
    chat_sessions_dir = workspace_dir / "chatSessions"
    chat_sessions_dir.mkdir(parents=True)
    
    # Create test session file
    session_data = {
        "version": 3,
        "sessionId": "integration-test-001",
        "creationDate": "2026-03-31T10:00:00.000Z",
        "lastMessageDate": "2026-03-31T10:05:00.000Z",
        "requests": [
            {
                "requestId": "req-001",
                "timestamp": "2026-03-31T10:00:00.000Z",
                "message": "How do I parse JSON in Python?",
                "response": [
                    {
                        "type": "text",
                        "value": "You can use the `json` module from the standard library."
                    }
                ]
            },
            {
                "requestId": "req-002",
                "timestamp": "2026-03-31T10:02:00.000Z",
                "message": "Can you show me an example?",
                "response": [
                    {
                        "type": "codeBlock",
                        "language": "python",
                        "content": "import json\\ndata = json.loads('{\"key\": \"value\"}')"
                    }
                ]
            }
        ]
    }
    
    session_file = chat_sessions_dir / "test-session.json"
    session_file.write_text(json.dumps(session_data))
    
    # Execute workflow
    workspaces = discover_workspaces(tmp_path)
    assert len(workspaces) == 1
    assert len(workspaces[0].session_files) == 1
    
    # Parse sessions
    sessions = []
    for workspace in workspaces:
        for session_file in workspace.session_files:
            session = parse_session_file(session_file)
            sessions.append(session)
    
    assert len(sessions) == 1
    assert len(sessions[0].messages) == 4  # 2 user + 2 assistant
    
    # Generate HTML
    formatter = HTMLFormatter(sessions=sessions)
    html_output = formatter.generate()
    
    # Verify HTML completeness
    assert "<!DOCTYPE html>" in html_output
    assert "integration-test-001" in html_output
    assert "How do I parse JSON in Python?" in html_output
    assert "json" in html_output.lower()
    assert "import json" in html_output
    assert "Can you show me an example?" in html_output

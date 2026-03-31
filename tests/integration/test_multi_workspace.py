"""Integration tests for multi-workspace parsing and labeling."""

import json
from pathlib import Path

import pytest

from chat_history_parser.scanner import discover_workspaces
from chat_history_parser.parser import parse_session_file


def test_parse_multiple_workspaces_separate_labels(tmp_path):
    """Test that sessions from different workspaces are correctly labeled.
    
    When parsing multiple workspaces:
    - Each session should have workspace_id attribute
    - Sessions should be grouped/identifiable by workspace
    - Output should distinguish between workspaces
    """
    # Create two workspaces with different sessions
    ws1_id = "aaaa" + "a" * 28
    ws2_id = "bbbb" + "b" * 28
    
    # Workspace 1 sessions
    ws1_sessions_dir = tmp_path / ws1_id / "chatSessions"
    ws1_sessions_dir.mkdir(parents=True)
    
    session1 = {
        "version": 3,
        "sessionId": "ws1-session1",
        "creationDate": "2026-03-31T10:00:00.000Z",
        "requests": [
            {
                "requestId": "req-1",
                "timestamp": "2026-03-31T10:00:00.000Z",
                "message": "Message from workspace 1",
                "response": [{"type": "text", "value": "Response 1"}]
            }
        ]
    }
    (ws1_sessions_dir / "session1.json").write_text(json.dumps(session1))
    
    # Workspace 2 sessions
    ws2_sessions_dir = tmp_path / ws2_id / "chatSessions"
    ws2_sessions_dir.mkdir(parents=True)
    
    session2 = {
        "version": 3,
        "sessionId": "ws2-session1",
        "creationDate": "2026-03-31T11:00:00.000Z",
        "requests": [
            {
                "requestId": "req-2",
                "timestamp": "2026-03-31T11:00:00.000Z",
                "message": "Message from workspace 2",
                "response": [{"type": "text", "value": "Response 2"}]
            }
        ]
    }
    (ws2_sessions_dir / "session2.json").write_text(json.dumps(session2))
    
    # Discover workspaces
    workspaces = discover_workspaces(tmp_path)
    
    assert len(workspaces) == 2
    
    # Parse all sessions with workspace_id labels
    all_sessions = []
    
    for workspace in workspaces:
        for session_file in workspace.session_files:
            session = parse_session_file(session_file, workspace.workspace_id)
            if session:
                all_sessions.append(session)
    
    # Verify all sessions parsed
    assert len(all_sessions) == 2
    
    # Verify workspace IDs are attached
    assert all(hasattr(session, 'workspace_id') for session in all_sessions)
    assert all(session.workspace_id is not None for session in all_sessions)
    
    # Verify sessions can be grouped by workspace
    ws1_sessions = [s for s in all_sessions if s.workspace_id == ws1_id]
    ws2_sessions = [s for s in all_sessions if s.workspace_id == ws2_id]
    
    assert len(ws1_sessions) == 1
    assert len(ws2_sessions) == 1
    
    # Verify session content matches workspace
    assert ws1_sessions[0].session_id == "ws1-session1"
    assert ws2_sessions[0].session_id == "ws2-session1"
    
    # Verify messages can be traced to workspace
    assert len(ws1_sessions[0].messages) >= 1
    assert "workspace 1" in ws1_sessions[0].messages[0].content
    
    assert len(ws2_sessions[0].messages) >= 1
    assert "workspace 2" in ws2_sessions[0].messages[0].content


def test_workspace_filtering_by_id(tmp_path):
    """Test filtering to a specific workspace ID during parsing."""
    # Create three workspaces
    ws_ids = ["a" * 32, "b" * 32, "c" * 32]
    
    for ws_id in ws_ids:
        sessions_dir = tmp_path / ws_id / "chatSessions"
        sessions_dir.mkdir(parents=True)
        
        session = {
            "version": 3,
            "sessionId": f"session-{ws_id[:4]}",
            "requests": []
        }
        (sessions_dir / "test.json").write_text(json.dumps(session))
    
    # Discover all workspaces
    all_workspaces = discover_workspaces(tmp_path)
    assert len(all_workspaces) == 3
    
    # Filter to specific workspace
    target_ws_id = "b" * 32
    filtered_workspaces = [w for w in all_workspaces if w.workspace_id == target_ws_id]
    
    assert len(filtered_workspaces) == 1
    assert filtered_workspaces[0].workspace_id == target_ws_id

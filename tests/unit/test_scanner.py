"""Unit tests for workspace scanner - multi-workspace discovery."""

import json


from chat_history_parser.scanner import discover_workspaces


def test_discover_multiple_workspaces(tmp_path):
    """Test discovery of multiple workspace directories.
    
    WorkspaceStorage can contain multiple workspace folders with IDs
    matching pattern: [0-9a-f]{32} (32-character hex string)
    """
    # Create multiple workspace directories
    workspace1_id = "a" * 32
    workspace2_id = "b" * 32
    workspace3_id = "c" * 32
    invalid_id = "not-a-workspace"
    
    # Create valid workspaces with chatSessions
    for ws_id in [workspace1_id, workspace2_id, workspace3_id]:
        sessions_dir = tmp_path / ws_id / "chatSessions"
        sessions_dir.mkdir(parents=True)
        
        # Add a sample session file
        session = {
            "version": 3,
            "sessionId": f"session-{ws_id[:4]}",
            "creationDate": "2026-03-31T10:00:00.000Z",
            "requests": []
        }
        (sessions_dir / "sample.json").write_text(json.dumps(session))
    
    # Create invalid directory (won't be discovered)
    invalid_dir = tmp_path / invalid_id / "chatSessions"
    invalid_dir.mkdir(parents=True)
    
    # Discover workspaces
    workspaces = discover_workspaces(tmp_path)
    
    # Should find exactly 3 valid workspaces
    assert len(workspaces) == 3
    
    # Verify workspace IDs are all 32-character hex strings
    ws_ids = [w.workspace_id for w in workspaces]
    assert workspace1_id in ws_ids
    assert workspace2_id in ws_ids
    assert workspace3_id in ws_ids
    assert invalid_id not in ws_ids
    
    # Each workspace should have at least one session file
    for workspace in workspaces:
        assert len(workspace.session_files) >= 1


def test_workspace_id_extraction(tmp_path):
    """Test correct extraction of workspace ID from directory path.
    
    Workspace ID should be the 32-char hex directory name containing chatSessions/.
    """
    workspace_id = "1234567890abcdef1234567890abcdef"
    sessions_dir = tmp_path / workspace_id / "chatSessions"
    sessions_dir.mkdir(parents=True)
    
    # Add sample session
    session = {
        "version": 3,
        "sessionId": "test",
        "requests": []
    }
    (sessions_dir / "test.json").write_text(json.dumps(session))
    
    # Discover workspaces
    workspaces = discover_workspaces(tmp_path)
    
    assert len(workspaces) == 1
    assert workspaces[0].workspace_id == workspace_id
    assert workspaces[0].base_path == tmp_path / workspace_id


def test_discover_nested_in_vscode_workspace_storage(tmp_path):
    """Test discovering workspaces nested in typical VS Code structure.
    
    Typical structure:
    /home/user/.config/Code/User/workspaceStorage/
        ├── 1234567890abcdef1234567890abcdef/
        │   └── chatSessions/
        │       └── abc123.json
        └── fedcba0987654321fedcba0987654321/
            └── chatSessions/
                └── def456.json
    """
    # Simulate typical VS Code WorkspaceStorage structure
    ws1_id = "f" * 32
    ws2_id = "e" * 32
    
    # Create two workspaces
    (tmp_path / ws1_id / "chatSessions").mkdir(parents=True)
    (tmp_path / ws2_id / "chatSessions").mkdir(parents=True)
    
    # Add sessions to each
    for ws_id in [ws1_id, ws2_id]:
        session = {
            "version": 3,
            "sessionId": f"session-{ws_id[:4]}",
            "requests": []
        }
        sessions_dir = tmp_path / ws_id / "chatSessions"
        (sessions_dir / "abc.json").write_text(json.dumps(session))
    
    # Discover workspaces
    workspaces = discover_workspaces(tmp_path)
    
    # Should find both workspaces
    assert len(workspaces) == 2
    
    # Verify both have correct IDs
    ws_ids = {w.workspace_id for w in workspaces}
    assert ws1_id in ws_ids
    assert ws2_id in ws_ids
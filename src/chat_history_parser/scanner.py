"""Workspace scanning and chat session file discovery."""

import json
import re
from pathlib import Path

from chat_history_parser.errors import WorkspaceNotFoundError
from chat_history_parser.models import WorkspaceContext


def discover_workspaces(base_path: Path) -> list[WorkspaceContext]:
    """Discover all VS Code workspaces in a WorkspaceStorage directory.
    
    Scans for workspace directories matching the pattern [0-9a-f]{32} and
    finds all chatSessions JSON files within each workspace.
    
    Args:
        base_path: Path to WorkspaceStorage directory
        
    Returns:
        List of WorkspaceContext objects, one per discovered workspace
        
    Raises:
        WorkspaceNotFoundError: If base_path doesn't exist or isn't a directory
    """
    if not base_path.exists():
        raise WorkspaceNotFoundError(str(base_path))
    
    if not base_path.is_dir():
        raise WorkspaceNotFoundError(str(base_path))
    
    workspaces = []
    workspace_pattern = re.compile(r"^[0-9a-f]{32}$")
    
    # Check if base_path itself is a workspace directory
    if workspace_pattern.match(base_path.name):
        # Single workspace mode
        session_files = find_session_files(base_path)
        if session_files:  # Only add if sessions exist
            workspace_name = extract_workspace_name(base_path)
            workspaces.append(WorkspaceContext(
                workspace_id=base_path.name,
                base_path=base_path,
                session_files=session_files,
                workspace_name=workspace_name,
            ))
    else:
        # Multi-workspace mode - scan for workspace directories
        for item in base_path.iterdir():
            if item.is_dir() and workspace_pattern.match(item.name):
                session_files = find_session_files(item)
                if session_files:  # Only add if sessions exist
                    workspace_name = extract_workspace_name(item)
                    workspaces.append(WorkspaceContext(
                        workspace_id=item.name,
                        base_path=item,
                        session_files=session_files,
                        workspace_name=workspace_name,
                    ))
    
    return workspaces


def find_session_files(workspace_path: Path) -> list[Path]:
    """Find all chatSessions JSON and JSONL files in a workspace directory.
    
    Looks for files matching the patterns: chatSessions/*.json and chatSessions/*.jsonl
    
    Args:
        workspace_path: Path to a single workspace directory
        
    Returns:
        List of Path objects for discovered session files (sorted by name)
    """
    chat_sessions_dir = workspace_path / "chatSessions"
    
    if not chat_sessions_dir.exists() or not chat_sessions_dir.is_dir():
        return []
    
    # Find all JSON and JSONL files in chatSessions directory
    json_files = list(chat_sessions_dir.glob("*.json"))
    jsonl_files = list(chat_sessions_dir.glob("*.jsonl"))
    session_files = sorted(json_files + jsonl_files)
    
    return session_files


def extract_workspace_name(workspace_path: Path) -> str | None:
    """Extract workspace name from workspace.json file.
    
    Reads workspace.json and extracts the full folder path from the 'folder' field.
    Supports file:// and vscode-remote:// URI schemes.
    Example: {"folder": "file:///home/user/myproject"} -> "/home/user/myproject"
    Example: {"folder": "vscode-remote://wsl%2Bdebian/home/benoit/resc/frontend"} -> "/home/benoit/resc/frontend"
    
    Args:
        workspace_path: Path to workspace directory
        
    Returns:
        Full workspace folder path or None if workspace.json is missing/invalid
    """
    workspace_json_path = workspace_path / "workspace.json"
    
    if not workspace_json_path.exists():
        return None
    
    try:
        with open(workspace_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        folder_uri = data.get('folder', '')
        if not folder_uri:
            return None
        
        # Extract full folder path from file:// URI
        # Example: "file:///home/user/myproject" -> "/home/user/myproject"
        if folder_uri.startswith('file://'):
            folder_path = folder_uri[7:]  # Remove 'file://' prefix
            return folder_path

        # Extract path from vscode-remote:// URI (WSL, SSH, etc.)
        # Example: "vscode-remote://wsl%2Bdebian/home/benoit/resc/frontend" -> "/home/benoit/resc/frontend"
        if folder_uri.startswith('vscode-remote://'):
            from urllib.parse import urlparse, unquote
            parsed = urlparse(folder_uri)
            return unquote(parsed.path)

        return None
    
    except (json.JSONDecodeError, OSError, KeyError):
        # If workspace.json is malformed or unreadable, return None
        return None

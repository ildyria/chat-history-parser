"""Integration tests for single-file CLI parsing mode."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_parse_single_file_json_stdout():
    """Test parsing a single session file with --session-file to stdout."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "chat_history_parser",
            "--session-file",
            "tests/fixtures/sample-session-valid.json",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert result.stdout, "No output to stdout"

    data = json.loads(result.stdout)
    assert "metadata" in data
    assert "sessions" in data
    assert data["metadata"]["session_count"] == 1
    assert len(data["sessions"]) == 1


def test_parse_single_file_json_output_file(tmp_path):
    """Test parsing a single session file with --session-file and writing to -o path."""
    output_file = tmp_path / "single-output.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "chat_history_parser",
            "--session-file",
            "tests/fixtures/sample-session-valid.json",
            "--format",
            "json",
            "-o",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert output_file.exists(), "Expected output file to be created"

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "metadata" in data
    assert "sessions" in data
    assert data["metadata"]["session_count"] == 1


def test_session_file_conflicts_with_workspace_options():
    """Test --session-file rejects workspace-only options."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "chat_history_parser",
            "--session-file",
            "tests/fixtures/sample-session-valid.json",
            "--list-workspaces",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 2
    assert "cannot be used with --session-file" in result.stderr.lower()

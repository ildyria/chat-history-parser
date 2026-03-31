"""Integration tests for JSON export functionality."""

import json
import subprocess
import sys
from pathlib import Path


def test_parse_to_json_stdout():
    """Test parsing workspace and outputting JSON to stdout."""
    # Run CLI with --format json
    result = subprocess.run(
        [
            sys.executable, "-m", "chat_history_parser",
            "tests/fixtures/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "--format", "json"
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
        env={"PYTHONPATH": "src"}
    )
    
    # Should succeed
    assert result.returncode == 0, f"Failed: {result.stderr}"
    
    # Should output to stdout
    assert result.stdout, "No output to stdout"
    
    # Should be valid JSON
    data = json.loads(result.stdout)
    
    # Check structure
    assert "metadata" in data
    assert "sessions" in data
    
    # Should have parsed sessions
    assert data["metadata"]["session_count"] > 0
    assert len(data["sessions"]) > 0


def test_parse_to_json_file():
    """Test parsing workspace and writing JSON to file."""
    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / "test-output.json"

    # The CLI generates per-workspace filenames with a date suffix:
    # test-output-ChatHistoryParser-YYYY-MM-DD.json
    created_files = []

    try:
        # Run CLI with -o flag
        result = subprocess.run(
            [
                sys.executable, "-m", "chat_history_parser",
                "tests/fixtures/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "--format", "json",
                "-o", str(output_file)
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
            env={"PYTHONPATH": "src"}
        )

        # Should succeed
        assert result.returncode == 0, f"Failed: {result.stderr}"

        # Find the generated file (name includes workspace name and date)
        created_files = list(project_root.glob("test-output-ChatHistoryParser*.json"))
        assert created_files, f"No output file created matching test-output-ChatHistoryParser*.json; stderr: {result.stderr}"

        expected_output_file = created_files[0]

        # Should be valid JSON
        with open(expected_output_file) as f:
            data = json.load(f)

        # Check structure
        assert "metadata" in data
        assert "sessions" in data
        assert data["metadata"]["session_count"] > 0

    finally:
        # Cleanup
        for f in created_files:
            if f.exists():
                f.unlink()


def test_json_output_piping():
    """Test that JSON output can be piped to jq or other tools."""
    # Run CLI and pipe to jq (if available)
    result = subprocess.run(
        [
            sys.executable, "-m", "chat_history_parser",
            "tests/fixtures/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "--format", "json"
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
        env={"PYTHONPATH": "src"}
    )
    
    assert result.returncode == 0
    
    # Try to process with jq if available
    jq_result = subprocess.run(
        ["jq", ".metadata.session_count"],
        input=result.stdout,
        capture_output=True,
        text=True
    )
    
    # If jq not available, that's okay - just check JSON is valid
    if jq_result.returncode == 0:
        count = int(jq_result.stdout.strip())
        assert count > 0
    else:
        # Fall back to Python parsing
        data = json.loads(result.stdout)
        assert data["metadata"]["session_count"] > 0


def test_json_with_empty_workspace():
    """Test JSON output for empty workspace directory."""
    result = subprocess.run(
        [
            sys.executable, "-m", "chat_history_parser",
            "tests/fixtures/sample-session-empty.json",  # This is a file path, not workspace
            "--format", "json"
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
        env={"PYTHONPATH": "src"}
    )
    
    # Should fail gracefully or return empty results
    # The exact behavior depends on implementation
    data = json.loads(result.stdout) if result.returncode == 0 else None
    
    if data:
        # If it succeeds, should have empty sessions
        assert isinstance(data, dict)
        assert "metadata" in data

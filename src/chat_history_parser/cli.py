"""CLI argument parsing and main entry point."""

import argparse
import platform
import sys
from pathlib import Path

from chat_history_parser import __version__
from chat_history_parser.scanner import discover_workspaces
from chat_history_parser.parser import parse_session_file
from chat_history_parser.formatters.html_formatter import HTMLFormatter
from chat_history_parser.formatters.json_formatter import JSONFormatter
from chat_history_parser.models import FormatterContext, ParseError, ChatSession
from chat_history_parser.errors import WorkspaceNotFoundError, InvalidSessionFileError


def get_default_workspace_storage_path() -> Path | None:
    """Get the default VS Code workspaceStorage path based on the operating system.
    
    Returns:
        Path to the default workspaceStorage directory, or None if it cannot be determined.
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\Code\User\workspaceStorage
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "Code" / "User" / "workspaceStorage"
    elif system == "Darwin":
        # macOS: $HOME/Library/Application Support/Code/User/workspaceStorage
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage"
    elif system == "Linux":
        # Linux: $HOME/.config/Code/User/workspaceStorage
        return Path.home() / ".config" / "Code" / "User" / "workspaceStorage"
    
    return None


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance with all flags and options
    """
    parser = argparse.ArgumentParser(
        prog="chat-history-parser",
        description="Parse VS Code WorkspaceStorage chat session files into JSON and HTML formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use default VS Code location, output to stdout
  %(prog)s --list-workspaces                  # List all workspaces in default location
  %(prog)s -o output.html                     # Parse default location, save to file(s)
  %(prog)s /path/to/workspaceStorage -o out.html
  %(prog)s -p "ProjectName" -o output.html    # Filter by project name
  %(prog)s --format json | jq '.metadata'     # Pipe JSON to jq

For more information, see: https://github.com/your-repo/chat-history-parser
        """,
    )
    
    # Optional positional argument (defaults to OS-specific VS Code location)
    parser.add_argument(
        "workspace_path",
        type=str,
        nargs="?",
        help="Path to VS Code WorkspaceStorage directory (defaults to OS-specific VS Code location)",
    )
    
    # Output format
    parser.add_argument(
        "-f", "--format",
        choices=["json", "html"],
        default="html",
        help="Output format (default: html)",
    )
    
    # Output destination
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="PATH",
        help="Output file path (default: stdout)",
    )
    
    # HTML output mode
    parser.add_argument(
        "-m", "--html-mode",
        choices=["single", "per-session", "per-workspace"],
        default="single",
        help="HTML output structure: single file, one per session, or one per workspace (default: single)",
    )
    
    # Concatenation mode
    parser.add_argument(
        "-c", "--concatenate",
        action="store_true",
        help="Merge all sessions chronologically into a single conversation",
    )
    
    # Workspace filter by ID
    parser.add_argument(
        "-w", "--workspace",
        type=str,
        metavar="WORKSPACE_ID",
        help="Filter to specific workspace ID (32-character hex string)",
    )
    
    # Workspace filter by path
    parser.add_argument(
        "-p", "--workspace-path",
        type=str,
        metavar="PATH",
        dest="filter_path",
        help="Filter to workspaces matching this folder path (e.g., 'LycheeOrg' or '/home/user/Projects/LycheeOrg')",
    )
    
    # List workspaces
    parser.add_argument(
        "-l", "--list-workspaces",
        action="store_true",
        help="List all discovered workspaces with their details and exit",
    )
    
    # Version
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    return parser


def generate_output_filename(
    base_output: str | None,
    workspace_name: str | None,
    workspace_id: str,
    format_ext: str,
    session_date: str | None = None,
    session_id: str | None = None,
    used_filenames: set | None = None,
) -> str | None:
    """Generate output filename for a specific workspace.

    Creates workspace-specific filenames based on the -o argument:
    - No -o specified: Returns None (stdout mode)
    - -o output.html: Creates output-LycheeOrg.html, output-OtherProject.html
    - -o output: Creates output-LycheeOrg.html, output-OtherProject.html
    - -o output_dir/ (directory): Creates output_dir/LycheeOrg.html, output_dir/OtherProject.html

    Args:
        base_output: User-specified output path from -o flag (or None for stdout)
        workspace_name: Human-readable workspace name from workspace.json (or None)
        workspace_id: 32-char hex workspace ID (fallback if workspace_name is None)
        format_ext: Output format ('html' or 'json')
        session_date: Optional date prefix (YYYY-MM-DD) for per-session filenames
        session_id: Optional session ID suffix for per-session filenames
        used_filenames: Optional set of already-used filenames for deduplication

    Returns:
        Output filename for this workspace, or None if stdout mode
    """
    if base_output is None:
        # No -o specified: stdout mode
        return None
    
    # Use workspace name if available, otherwise use workspace ID
    # If workspace_name is a full path, extract just the basename for the filename
    if workspace_name:
        workspace_identifier = Path(workspace_name).name
    else:
        workspace_identifier = workspace_id

    # Build session-specific suffix when per-session info is provided
    if session_date and session_id:
        session_suffix = f"{session_date}-{session_id[:8]}"
    elif session_date:
        session_suffix = session_date
    elif session_id:
        session_suffix = session_id[:8]
    else:
        session_suffix = None

    # Parse the base output path
    output_path = Path(base_output)

    # Check if the path is an existing directory
    if output_path.is_dir():
        if session_suffix:
            base_filename = f"{workspace_identifier}-{session_suffix}.{format_ext}"
        else:
            base_filename = f"{workspace_identifier}.{format_ext}"
        result = str(output_path / base_filename)
        if used_filenames is not None:
            result = _deduplicate_filename(result, used_filenames)
            used_filenames.add(result)
        return result

    # Split into directory, stem, and suffix
    output_dir = output_path.parent
    output_stem = output_path.stem
    output_suffix = output_path.suffix

    # If no suffix provided, use the format
    if not output_suffix:
        output_suffix = f".{format_ext}"

    # Generate workspace-specific filename: stem-WorkspaceName[-session].ext
    if session_suffix:
        base_filename = f"{output_stem}-{workspace_identifier}-{session_suffix}{output_suffix}"
    else:
        base_filename = f"{output_stem}-{workspace_identifier}{output_suffix}"

    # Combine with directory
    if output_dir and str(output_dir) != '.':
        result = str(output_dir / base_filename)
    else:
        result = base_filename

    if used_filenames is not None:
        result = _deduplicate_filename(result, used_filenames)
        used_filenames.add(result)
    return result


def _deduplicate_filename(filepath: str, used: set) -> str:
    """Append a numeric suffix to filepath if it already exists in used."""
    if filepath not in used:
        return filepath
    path = Path(filepath)
    counter = 2
    while True:
        candidate = str(path.parent / f"{path.stem}-{counter}{path.suffix}")
        if candidate not in used:
            return candidate
        counter += 1


def list_workspaces(workspaces: list) -> None:
    """Display all discovered workspaces in a human-readable table format.
    
    Args:
        workspaces: List of WorkspaceContext objects to display
    """
    if not workspaces:
        print("No workspaces found.")
        return
    
    print(f"\nFound {len(workspaces)} workspace(s):\n")
    print(f"{'Workspace ID':<34} {'Sessions':<10} {'Project Path'}")
    print("-" * 100)
    
    for ws in workspaces:
        workspace_id = ws.workspace_id
        session_count = len(ws.session_files)
        project_path = ws.workspace_name or "(no workspace.json)"
        
        print(f"{workspace_id:<34} {session_count:<10} {project_path}")
    
    print()


def main():
    """Main entry point for the CLI application."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Determine workspace path: use provided path or default VS Code location
    if args.workspace_path:
        workspace_path = Path(args.workspace_path).expanduser().resolve()
    else:
        default_path = get_default_workspace_storage_path()
        if default_path is None:
            print("Error: Could not determine default VS Code workspaceStorage path for your OS", file=sys.stderr)
            print("Please provide a path explicitly: chat-history-parser /path/to/workspaceStorage", file=sys.stderr)
            sys.exit(2)
        workspace_path = default_path
        if not workspace_path.exists():
            print(f"Error: Default VS Code workspaceStorage path not found: {workspace_path}", file=sys.stderr)
            print("Please provide a path explicitly: chat-history-parser /path/to/workspaceStorage", file=sys.stderr)
            sys.exit(1)
    
    try:
        # Discover workspaces
        workspaces = discover_workspaces(workspace_path)
        
        if not workspaces:
            print(f"Error: No chat sessions found in {workspace_path}", file=sys.stderr)
            print("Ensure the path contains chatSessions/ directories with JSON files.", file=sys.stderr)
            sys.exit(1)
        
        # Handle --list-workspaces mode
        if args.list_workspaces:
            list_workspaces(workspaces)
            sys.exit(0)
        
        # Filter by workspace ID if specified
        if args.workspace:
            workspaces = [w for w in workspaces if w.workspace_id == args.workspace]
            if not workspaces:
                print(f"Error: Workspace '{args.workspace}' not found", file=sys.stderr)
                sys.exit(1)
        
        # Filter by workspace path if specified
        if args.filter_path:
            # Convert filter_path argument to lowercase for case-insensitive matching
            search_path = args.filter_path.lower()
            filtered = []
            for ws in workspaces:
                if ws.workspace_name:
                    # Match against the full folder path from workspace.json
                    # Supports both partial matches (e.g., "LycheeOrg") and full paths
                    if search_path in ws.workspace_name.lower():
                        filtered.append(ws)
            
            workspaces = filtered
            if not workspaces:
                print(f"Error: No workspaces found matching path '{args.filter_path}'", file=sys.stderr)
                sys.exit(1)
        
        # Process each workspace separately to generate individual output files
        total_sessions = 0
        total_errors = 0
        output_files = []
        used_filenames = set()  # Track used filenames to prevent overwrites
        
        for workspace in workspaces:
            workspace_sessions = []
            workspace_parse_errors = []
            
            # T056: Enhanced stderr logging for parse errors
            for session_file in workspace.session_files:
                try:
                    session = parse_session_file(session_file, workspace.workspace_id)
                    
                    # T052: Handle None return (malformed JSON)
                    if session is None:
                        error_msg = f"Failed to parse {session_file.name}: malformed JSON"
                        print(f"ERROR: {error_msg}", file=sys.stderr)
                        workspace_parse_errors.append(ParseError(
                            file_path=str(session_file),
                            error_type="MalformedJSON",
                            message=error_msg
                        ))
                        continue
                    
                    workspace_sessions.append(session)
                    
                    # T055: Collect parse errors from session
                    if session.parse_errors:
                        for err_msg in session.parse_errors:
                            workspace_parse_errors.append(ParseError(
                                file_path=str(session_file),
                                error_type="RequestParseError",
                                message=err_msg
                            ))
                        
                except InvalidSessionFileError as e:
                    print(f"ERROR: {e}", file=sys.stderr)
                    workspace_parse_errors.append(ParseError(
                        file_path=str(session_file),
                        error_type="InvalidSessionFileError",
                        message=str(e)
                    ))
                    # Continue parsing other files
                except Exception as e:
                    error_msg = f"Unexpected error parsing {session_file.name}: {e}"
                    print(f"ERROR: {error_msg}", file=sys.stderr)
                    workspace_parse_errors.append(ParseError(
                        file_path=str(session_file),
                        error_type=type(e).__name__,
                        message=error_msg
                    ))
            
            # Skip workspace if no sessions were successfully parsed
            if not workspace_sessions:
                print(f"WARNING: No sessions parsed for workspace {workspace.workspace_id}", file=sys.stderr)
                continue
            
            # Report parsing summary per workspace
            if workspace_parse_errors:
                print(f"Workspace {workspace.workspace_name or workspace.workspace_id}: Parsed {len(workspace_sessions)} session(s), encountered {len(workspace_parse_errors)} error(s)", file=sys.stderr)
            else:
                print(f"Workspace {workspace.workspace_name or workspace.workspace_id}: Successfully parsed {len(workspace_sessions)} session(s)", file=sys.stderr)
            
            total_sessions += len(workspace_sessions)
            total_errors += len(workspace_parse_errors)
            
            # T072-T073: Concatenate sessions if flag is set
            if args.concatenate and len(workspace_sessions) > 1:
                print(f"Concatenating {len(workspace_sessions)} sessions for workspace {workspace.workspace_name or workspace.workspace_id}...", file=sys.stderr)
                workspace_sessions = [concatenate_sessions(workspace_sessions)]
            
            # Handle per-session mode: generate separate file for each session
            if args.html_mode == "per-session" and args.format == "html":
                for session in workspace_sessions:
                    # Get date prefix from session creation_date
                    session_date = None
                    if session.creation_date:
                        session_date = session.creation_date.strftime("%Y-%m-%d")
                    
                    # Generate HTML for single session
                    output_content = generate_html_output([session], "single")
                    
                    # Determine output file path for this session
                    output_file = generate_output_filename(
                        base_output=args.output,
                        workspace_name=workspace.workspace_name,
                        workspace_id=workspace.workspace_id,
                        format_ext=args.format,
                        session_date=session_date,
                        session_id=session.session_id,
                        used_filenames=used_filenames
                    )
                    
                    # Write output
                    write_output(output_content, output_file)
                    if output_file:
                        output_files.append(output_file)
            else:
                # Single file mode (default) or per-workspace mode
                # Create formatter context for this workspace
                context = FormatterContext(
                    workspace_path=str(workspace.base_path),
                    sessions=workspace_sessions,
                    parse_errors=workspace_parse_errors
                )
                
                # Generate output based on format
                if args.format == "html":
                    output_content = generate_html_output(workspace_sessions, args.html_mode)
                else:
                    output_content = generate_json_output(context)
                
                # Get date prefix from first session's creation_date
                session_date = None
                if workspace_sessions and workspace_sessions[0].creation_date:
                    session_date = workspace_sessions[0].creation_date.strftime("%Y-%m-%d")
                
                # Determine output file path for this workspace
                output_file = generate_output_filename(
                    base_output=args.output,
                    workspace_name=workspace.workspace_name,
                    workspace_id=workspace.workspace_id,
                    format_ext=args.format,
                    session_date=session_date,
                    used_filenames=used_filenames
                )
                
                # Write output
                write_output(output_content, output_file)
                output_files.append(output_file if output_file else "stdout")
        
        # T057: Partial success handling
        if total_sessions == 0:
            print("ERROR: No sessions could be parsed successfully", file=sys.stderr)
            if total_errors > 0:
                print(f"Total errors: {total_errors}", file=sys.stderr)
            sys.exit(1)
        
        # Final summary
        print(f"\nSummary: Processed {len(workspaces)} workspace(s), {total_sessions} session(s) total", file=sys.stderr)
        if total_errors > 0:
            print(f"Total parse errors: {total_errors}", file=sys.stderr)
        print(f"Generated {len(output_files)} output file(s):", file=sys.stderr)
        for output_file in output_files:
            print(f"  - {output_file}", file=sys.stderr)
        
        # Exit with success
        sys.exit(0)
        
    except WorkspaceNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def generate_html_output(sessions: list, html_mode: str) -> str:
    """Generate HTML output from parsed sessions.
    
    Args:
        sessions: List of ChatSession objects
        html_mode: Output mode ('single', 'per-session', 'per-workspace')
        
    Returns:
        HTML content as string
    """
    formatter = HTMLFormatter(sessions=sessions, mode=html_mode)
    return formatter.generate()


def concatenate_sessions(sessions: list[ChatSession]) -> ChatSession:
    """Concatenate multiple sessions chronologically into a single virtual session.
    
    T073: Merge all messages from all sessions, sorted by timestamp.
    
    Args:
        sessions: List of ChatSession objects to merge
        
    Returns:
        Single ChatSession with all messages merged chronologically
    """
    if not sessions:
        raise ValueError("Cannot concatenate empty session list")
    
    # Collect all messages from all sessions
    all_messages = []
    all_errors = []
    
    for session in sessions:
        all_messages.extend(session.messages)
        all_errors.extend(session.parse_errors)
    
    # Sort messages chronologically
    # Handle messages with None timestamps by placing them at the end
    # Use timestamp or epoch for sorting to avoid timezone comparison issues
    def sort_key(msg):
        if msg.timestamp is None:
            return float('inf')
        return msg.timestamp.timestamp()  # Convert to Unix timestamp for comparison
    
    all_messages.sort(key=sort_key)
    
    # Create merged session
    merged_session_id = f"concatenated_{len(sessions)}_sessions"
    
    # Use the earliest creation date
    creation_dates = [s.creation_date for s in sessions if s.creation_date]
    earliest_date = None
    if creation_dates:
        # Use timestamp comparison to avoid timezone issues
        earliest_date = min(creation_dates, key=lambda d: d.timestamp())
    
    # Use first session's source file
    source_file = sessions[0].source_file
    
    return ChatSession(
        session_id=merged_session_id,
        source_file=source_file,
        messages=all_messages,
        parse_errors=all_errors,
        creation_date=earliest_date,
        workspace_id=None,  # Multi-workspace concatenation loses workspace context
    )


def generate_json_output(context: FormatterContext) -> str:
    """Generate JSON output from formatter context.
    
    Args:
        context: FormatterContext with sessions and parse errors
        
    Returns:
        JSON content as string
    """
    formatter = JSONFormatter()
    return formatter.generate(context)


def write_output(content: str, output_path: str | None):
    """Write content to file or stdout.
    
    Args:
        content: Content string to write
        output_path: File path to write to, or None for stdout
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        if output_path:
            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(content, encoding='utf-8')
            print(f"Output written to: {output_file}", file=sys.stderr)
        else:
            # Write to stdout
            print(content)
            
    except IOError as e:
        print(f"Error: Failed to write output: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

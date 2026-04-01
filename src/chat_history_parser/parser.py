"""Core chat session file parsing logic."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from chat_history_parser.models import ChatSession, Message


def parse_session_file(file_path: Path, workspace_id: str | None = None) -> ChatSession | None:
    """Parse a chatSessions JSON file and extract conversation data.
    
    Expects schema v3 with structure:
    {
        "version": 3,
        "sessionId": "...",
        "creationDate": "ISO 8601 timestamp",
        "requests": [...]
    }
    
    Enhanced error handling (Phase 5):
    - Returns None on malformed JSON instead of raising
    - Uses defensive dict.get() for optional fields
    - Validates and provides fallbacks for timestamps
    - Continues parsing even if individual requests fail
    
    Args:
        file_path: Path to chatSessions JSON file
        workspace_id: Optional workspace identifier for multi-workspace scenarios
        
    Returns:
        ChatSession object with extracted messages, or None if file is unreadable
    """
    # T052: Try/except with specific error handling for JSON parsing
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        # Log error and return None instead of crashing
        print(f"ERROR: Malformed JSON in {file_path}: {e}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"ERROR: Cannot read file {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error reading {file_path}: {e}", file=sys.stderr)
        return None
    
    # T053: Defensive field access with dict.get() for optional fields
    session_id = data.get("sessionId", "unknown")
    requester_username = data.get("requesterUsername")
    responder_username = data.get("responderUsername")
    requester_avatar_url = _parse_avatar_uri(data.get("requesterAvatarIconUri"))
    _responder_uri = data.get("responderAvatarIconUri") or {}
    responder_avatar_url = _parse_avatar_uri(_responder_uri)
    responder_avatar_icon_id = _responder_uri.get("id") if isinstance(_responder_uri, dict) else None
    
    # Check for missing required fields
    if "version" not in data:
        print(f"WARNING: Missing version field in {file_path}, assuming v3", file=sys.stderr)
    
    if session_id == "unknown":
        print(f"WARNING: Missing sessionId in {file_path}", file=sys.stderr)
    
    # T054: Timestamp validation and fallback
    creation_date_str = data.get("creationDate")
    creation_date = None
    
    if creation_date_str:
        creation_date = _parse_timestamp(creation_date_str)
        if creation_date is None:
            print(f"WARNING: Invalid creationDate in {file_path}", file=sys.stderr)
    
    # Extract messages from requests array
    messages = []
    parse_errors = []
    requests = data.get("requests", [])
    
    for i, request in enumerate(requests):
        try:
            # Extract user message
            user_msg = extract_user_message(request)
            if user_msg:
                messages.append(user_msg)
            
            # Extract assistant messages
            assistant_msgs = extract_assistant_messages(request)
            messages.extend(assistant_msgs)
            
        except Exception as e:
            error_msg = f"Error parsing request {i}: {e}"
            parse_errors.append(error_msg)
            print(f"Warning: {error_msg}", file=sys.stderr)
    
    # Sort messages chronologically; messages with no timestamp go last
    messages.sort(key=lambda m: m.timestamp.timestamp() if m.timestamp else float('inf'))
    
    return ChatSession(
        session_id=session_id,
        source_file=file_path,
        messages=messages,
        parse_errors=parse_errors,
        creation_date=creation_date,
        workspace_id=workspace_id,
        requester_username=requester_username,
        responder_username=responder_username,
        requester_avatar_url=requester_avatar_url,
        responder_avatar_url=responder_avatar_url,
        responder_avatar_icon_id=responder_avatar_icon_id,
    )


def extract_user_message(request: dict) -> Message | None:
    """Extract user message from a request object.
    
    User message is found in request.message field, which can be:
    - A string (simple text)
    - An object with 'text' field (structured message)
    
    Args:
        request: Request dict from chatSessions JSON
        
    Returns:
        Message object with role='user' or None if no message
    """
    message_field = request.get("message")
    if not message_field:
        return None
    
    # Handle both string and object formats
    if isinstance(message_field, str):
        message_text = message_field
    elif isinstance(message_field, dict):
        message_text = message_field.get("text", "")
    else:
        return None
    
    if not message_text or not message_text.strip():
        return None
    
    timestamp_str = request.get("timestamp")
    timestamp = _parse_timestamp(timestamp_str)
    
    return Message(
        content=message_text.strip(),
        timestamp=timestamp,
        role="user",
    )


def extract_assistant_messages(request: dict) -> list[Message]:
    """Extract assistant messages from request.response array.
    
    Response array contains mixed types that need to be flattened:
    - text: Extract value field
    - tool invocations: Describe action
    - code blocks: Extract content
    - confirmations: Convert to text
    
    Args:
        request: Request dict from chatSessions JSON
        
    Returns:
        List of Message objects with role='assistant'
    """
    response_array = request.get("response", [])
    if not response_array:
        return []
    
    timestamp_str = request.get("timestamp")
    
    return flatten_response(response_array, timestamp_str)


def flatten_response(response_array: list, timestamp: str | None) -> list[Message]:
    """Flatten heterogeneous response array into readable text messages.

    Handles different response types (via 'type' field) and kinds (via 'kind' field):
    - text: Direct text content
    - toolInvocation: Describe the tool action
    - codeBlock: Format code with language
    - confirmation: Convert to descriptive text
    - textEditGroup: Reconstruct file content from line edits
    - Other types: Convert to string representation

    Args:
        response_array: List of response objects
        timestamp: ISO 8601 timestamp string

    Returns:
        List of Message objects with flattened content
    """
    messages = []
    parsed_timestamp = _parse_timestamp(timestamp)
    last_was_inline_ref = False

    for item in response_array:
        if not isinstance(item, dict):
            continue

        # Some items use 'kind' instead of 'type' (e.g. textEditGroup)
        response_type = item.get("type") or item.get("kind", "unknown")
        content = None

        if response_type == "text":
            content = item.get("value", "")

        elif response_type == "toolInvocation":
            tool_name = item.get("name", "unknown_tool")
            parameters = item.get("parameters", {})
            result = item.get("result")

            content = f"[Tool: {tool_name}]\n"
            if parameters:
                content += f"Parameters: {json.dumps(parameters, indent=2)}\n"
            if result:
                content += f"Result: {result}"

        elif response_type == "codeBlock":
            language = item.get("language", "")
            code_content = item.get("content", "")
            content = f"```{language}\n{code_content}\n```"

        elif response_type == "confirmation":
            title = item.get("title", "")
            message_obj = item.get("message", "")
            if isinstance(message_obj, dict):
                message_text = message_obj.get("value", "")
            else:
                message_text = message_obj or ""
            # Strip markdown links like [label](command:...) — keep just the label
            message_text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', message_text)
            content = f"[Confirmation: {title}]\n{message_text}" if message_text else f"[Confirmation: {title}]"

        elif response_type == "textEditGroup":
            content = _format_text_edit_group(item)

        elif response_type == "codeblockUri":
            uri = item.get("uri", {})
            file_path = uri.get("fsPath") or uri.get("path") or "unknown file"
            action = "Editing" if item.get("isEdit") else "Referencing"
            content = f"[{action}: {file_path}]"

        elif response_type == "inlineReference":
            ref = item.get("inlineReference", {})
            file_path = ref.get("fsPath") or ref.get("path") or "unknown file"
            inline = f" [File: {file_path}]"
            if messages:
                messages[-1] = Message(
                    content=messages[-1].content + inline,
                    timestamp=messages[-1].timestamp,
                    role=messages[-1].role,
                )
            last_was_inline_ref = True
            continue

        elif response_type in ("prepareToolInvocation", "undoStop"):
            # Internal Copilot bookkeeping — not meaningful to the reader
            content = None

        elif response_type == "toolInvocationSerialized":
            if item.get("presentation") == "hidden":
                content = None
            else:
                raw_msg = item.get("invocationMessage", item.get("toolId", ""))
                # invocationMessage may be a dict with a 'value' key
                if isinstance(raw_msg, dict):
                    raw_msg = raw_msg.get("value", "")
                # For terminal tool invocations, append the command line
                tool_data = item.get("toolSpecificData", {})
                if isinstance(tool_data, dict) and tool_data.get("kind") == "terminal":
                    cmd = tool_data.get("commandLine", {})
                    if isinstance(cmd, dict):
                        cmd_str = cmd.get("original") or cmd.get("value") or ""
                    else:
                        cmd_str = str(cmd) if cmd else ""
                    if cmd_str:
                        raw_msg = f"{raw_msg}: {cmd_str}" if raw_msg else cmd_str
                content = f"[Tool: {raw_msg}]" if raw_msg else None

        elif "value" in item:
            # No type/kind but has a value field — treat as plain text
            content = item.get("value", "")

        else:
            # Truly unknown — convert to string as last resort
            content = f"[{response_type}]: {json.dumps(item)}"

        stripped = content.strip() if content else ""
        # Skip empty, bare code-fence markers, and punctuation-only noise (e.g. " : ")
        if stripped and stripped.strip("`").strip() and re.search(r'\w', stripped):
            if last_was_inline_ref and messages:
                # Continuation after an inlineReference — append to the same message
                messages[-1] = Message(
                    content=messages[-1].content + " " + stripped,
                    timestamp=messages[-1].timestamp,
                    role=messages[-1].role,
                )
            else:
                messages.append(Message(
                    content=stripped,
                    timestamp=parsed_timestamp,
                    role="assistant",
                ))
        last_was_inline_ref = False
    
    return messages


def _format_text_edit_group(item: dict) -> str:
    """Format a textEditGroup response item as readable file content.

    textEditGroup represents Copilot writing a file. It contains a URI (the
    target file) and a nested array of line edits, each with a 'text' value
    and a 'range' indicating which line it belongs to.

    The edits are reconstructed into the resulting file content, sorted by
    line number, so the output is human-readable.

    Args:
        item: textEditGroup dict from the response array

    Returns:
        Formatted string showing the file path and its reconstructed content
    """
    # Extract file path from the URI object
    uri = item.get("uri", {})
    file_path = uri.get("fsPath") or uri.get("path") or "unknown file"

    # edits is a list of lists; each inner list has 0 or 1 edit dicts
    raw_edits = item.get("edits", [])

    # Flatten, keep only dicts that have both text and range
    flat_edits = [
        edit
        for group in raw_edits
        for edit in (group if isinstance(group, list) else [group])
        if isinstance(edit, dict) and "range" in edit
    ]

    # Sort by startLineNumber so output is in file order
    flat_edits.sort(key=lambda e: e.get("range", {}).get("startLineNumber", 0))

    lines = [edit.get("text", "") for edit in flat_edits]
    file_content = "\n".join(lines)

    # Detect language from extension for the code fence
    ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""

    return f"[File Edit: {file_path}]\n```{ext}\n{file_content}\n```"


def _parse_timestamp(timestamp_str: str | None) -> datetime | None:
    """Parse ISO 8601 timestamp string or Unix timestamp into datetime object.
    
    Handles:
    - ISO 8601 strings: "2026-03-31T10:00:00.000Z"
    - Unix timestamps in milliseconds: 1750796998325
    - Unix timestamps in seconds: 1750796998
    
    T054: Enhanced validation - returns None if parsing fails instead of fallback
    
    Args:
        timestamp_str: Timestamp string or number
        
    Returns:
        datetime object, or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    # Try parsing as ISO 8601 string
    if isinstance(timestamp_str, str):
        try:
            # Handle both 'Z' suffix and timezone offsets
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
        
        # Try parsing as Unix timestamp string
        try:
            timestamp_num = float(timestamp_str)
            # If > 10 digits, it's in milliseconds
            if timestamp_num > 10000000000:
                return datetime.fromtimestamp(timestamp_num / 1000)
            else:
                return datetime.fromtimestamp(timestamp_num)
        except (ValueError, OSError):
            pass
    
    # Try parsing as number (Unix timestamp)
    if isinstance(timestamp_str, (int, float)):
        try:
            # If > 10 digits, it's in milliseconds
            if timestamp_str > 10000000000:
                return datetime.fromtimestamp(timestamp_str / 1000)
            else:
                return datetime.fromtimestamp(timestamp_str)
        except (ValueError, OSError):
            pass
    
    # T054: Return None on parse failure instead of fallback
    return None


def _parse_avatar_uri(uri: dict | None) -> str | None:
    """Reconstruct an avatar URL from a VS Code URI object.

    The requesterAvatarIconUri field is stored as a decomposed URI:
    {
        "scheme": "https",
        "authority": "avatars.githubusercontent.com",
        "path": "/u/627094",
        "query": "v=4"
    }

    The responderAvatarIconUri for built-in icons looks like {"id": "copilot"}
    and has no reconstructable URL, so None is returned.

    Args:
        uri: URI object dict from chatSessions JSON, or None

    Returns:
        Reconstructed URL string, or None if not a network URI
    """
    if not uri or not isinstance(uri, dict):
        return None
    scheme = uri.get("scheme")
    authority = uri.get("authority")
    path = uri.get("path", "")
    query = uri.get("query")
    if scheme and authority:
        url = f"{scheme}://{authority}{path}"
        if query:
            url += f"?{query}"
        return url
    return None

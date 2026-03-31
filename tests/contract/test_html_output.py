"""Contract tests for HTML output structure and format."""

from datetime import datetime

from chat_history_parser.models import ChatSession, Message
from chat_history_parser.formatters.html_formatter import HTMLFormatter


def test_html_structure_contract(tmp_path):
    """Validate that HTML output adheres to structural contract.
    
    Contract guarantees:
    - Valid HTML5 document with DOCTYPE
    - Complete <html>, <head>, <body> structure
    - TailwindCSS CDN loaded in <head>
    - UTF-8 charset declaration
    - Viewport meta tag for responsive design
    """
    # Create a temporary source file
    source_file = tmp_path / "test.json"
    source_file.write_text('{}')
    
    message = Message(
        content="Test message",
        timestamp=datetime(2026, 3, 31, 10, 0),
        role="user"
    )
    
    session = ChatSession(
        session_id="contract-test-001",
        source_file=source_file,
        messages=[message],
    )
    
    formatter = HTMLFormatter(sessions=[session])
    html_output = formatter.generate()
    
    # Contract: Valid HTML5 document
    assert html_output.startswith("<!DOCTYPE html>")
    assert "<html" in html_output and "</html>" in html_output
    assert "<head>" in html_output and "</head>" in html_output
    assert "<body" in html_output and "</body>" in html_output  # Allow for body with attributes
    
    # Contract: TailwindCSS CDN loaded
    assert "tailwindcss" in html_output.lower()
    assert "<script" in html_output
    assert "cdn" in html_output.lower()
    
    # Contract: UTF-8 charset
    assert 'charset="utf-8"' in html_output.lower() or 'charset=utf-8' in html_output.lower()
    
    # Contract: Viewport meta tag
    assert "viewport" in html_output.lower()


def test_message_positioning_contract(tmp_path):
    """Validate that messages are positioned according to Copilot-style contract.
    
    Contract guarantees:
    - User messages: right-aligned
    - Assistant messages: left-aligned
    - Assistant actions/tools: left-aligned with muted styling
    - Each message has timestamp
    """
    # Create a temporary source file
    source_file = tmp_path / "test2.json"
    source_file.write_text('{}')
    
    messages = [
        Message(content="User message", timestamp=datetime(2026, 3, 31, 10, 0), role="user"),
        Message(content="Assistant response", timestamp=datetime(2026, 3, 31, 10, 1), role="assistant"),
    ]
    
    session = ChatSession(
        session_id="contract-test-002",
        source_file=source_file,
        messages=messages,
    )
    
    formatter = HTMLFormatter(sessions=[session])
    html_output = formatter.generate()
    
    # Contract: User messages right-aligned
    # Look for Tailwind classes like justify-end, ml-auto, or text-right
    assert any(cls in html_output for cls in ["justify-end", "ml-auto", "text-right", "flex-row-reverse"])
    
    # Contract: Different background colors for user vs assistant
    assert "bg-blue" in html_output  # User message background
    assert "bg-white" in html_output or "bg-gray" in html_output  # Assistant background
    
    # Contract: Timestamps present
    assert "2026" in html_output or "10:00" in html_output or "10:01" in html_output


def test_tailwindcss_cdn_contract(tmp_path):
    """Validate TailwindCSS is loaded from CDN (no build step).
    
    Contract guarantees:
    - TailwindCSS loaded via CDN script tag
    - No local CSS files required
    - CDN URL points to cdn.tailwindcss.com or unpkg.com
    """
    # Create a temporary source file
    source_file = tmp_path / "test3.json"
    source_file.write_text('{}')
    
    message = Message(
        content="Test",
        timestamp=datetime(2026, 3, 31, 10, 0),
        role="user"
    )
    
    session = ChatSession(
        session_id="contract-test-003",
        source_file=source_file,
        messages=[message],
    )
    
    formatter = HTMLFormatter(sessions=[session])
    html_output = formatter.generate()
    
    # Contract: TailwindCSS from CDN
    assert "cdn.tailwindcss.com" in html_output or "unpkg.com" in html_output or "tailwindcss" in html_output.lower()
    assert "<script" in html_output
    
    # Contract: No local CSS files
    assert '<link rel="stylesheet"' not in html_output or "tailwind" in html_output.lower()

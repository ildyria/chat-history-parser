"""Unit tests for HTML formatter with Copilot-style output."""

from datetime import datetime

from chat_history_parser.models import ChatSession, Message
from chat_history_parser.formatters.html_formatter import HTMLFormatter


def test_generate_single_file_html(tmp_path):
    """Test generation of single HTML file containing all sessions.
    
    Verifies:
    - Complete HTML document structure
    - TailwindCSS CDN script tag
    - All sessions included
    - Proper nesting of session/message elements
    """
    # Create a temporary source file
    source_file = tmp_path / "test.json"
    source_file.write_text('{}')
    
    # Create test sessions
    messages1 = [
        Message(content="Hello", timestamp=datetime(2026, 3, 31, 10, 0), role="user"),
        Message(content="Hi there!", timestamp=datetime(2026, 3, 31, 10, 1), role="assistant"),
    ]
    
    session1 = ChatSession(
        session_id="test-001",
        source_file=source_file,
        messages=messages1,
    )
    
    # Generate HTML
    formatter = HTMLFormatter(sessions=[session1], mode="single")
    html_output = formatter.generate()
    
    # Verify HTML structure
    assert "<!DOCTYPE html>" in html_output
    assert "<html" in html_output
    assert "</html>" in html_output
    assert "tailwindcss" in html_output.lower()  # TailwindCSS CDN
    assert "test-001" in html_output  # Session ID
    assert "Hello" in html_output  # User message
    assert "Hi there!" in html_output  # Assistant message


def test_user_message_right_aligned(tmp_path):
    """Test that user messages are right-aligned with blue background.
    
    Per spec: User messages should appear on the right side with bg-blue-100
    """
    # Create a temporary source file
    source_file = tmp_path / "test2.json"
    source_file.write_text('{}')
    
    message = Message(
        content="User question here",
        timestamp=datetime(2026, 3, 31, 10, 0),
        role="user"
    )
    
    session = ChatSession(
        session_id="test-001",
        source_file=source_file,
        messages=[message],
    )
    
    formatter = HTMLFormatter(sessions=[session])
    html_output = formatter.generate()
    
    # Check for right-aligned user message styling
    assert "justify-end" in html_output or "ml-auto" in html_output or "text-right" in html_output
    assert "bg-blue-100" in html_output or "bg-blue-50" in html_output
    assert "User question here" in html_output


def test_assistant_message_left_aligned(tmp_path):
    """Test that assistant messages are left-aligned with white/border background.
    
    Per spec: Assistant messages should appear on the left with bg-white and border
    """
    # Create a temporary source file
    source_file = tmp_path / "test3.json"
    source_file.write_text('{}')
    
    message = Message(
        content="Assistant response here",
        timestamp=datetime(2026, 3, 31, 10, 0),
        role="assistant"
    )
    
    session = ChatSession(
        session_id="test-001",
        source_file=source_file,
        messages=[message],
    )
    
    formatter = HTMLFormatter(sessions=[session])
    html_output = formatter.generate()
    
    # Check for left-aligned assistant message styling
    assert "justify-start" in html_output or "mr-auto" in html_output or "text-left" in html_output
    assert "bg-white" in html_output or "bg-gray-50" in html_output
    assert "border" in html_output
    assert "Assistant response here" in html_output

"""HTML output formatter with TailwindCSS styling."""

from datetime import datetime

from markdown_it import MarkdownIt

from chat_history_parser.models import ChatSession, Message


class HTMLFormatter:
    """Generate HTML output with GitHub Copilot-style chat interface.
    
    Features:
    - User messages: right-aligned with blue background
    - Assistant messages: left-aligned with white/bordered background
    - Actions/tools: left-aligned with gray muted background
    - TailwindCSS loaded via CDN (no build step)
    - Self-contained HTML files
    - Responsive design with dark mode support
    """
    
    def __init__(self, sessions: list[ChatSession], mode: str = "single"):
        """Initialize HTML formatter.
        
        Args:
            sessions: List of ChatSession objects to format
            mode: Output mode ('single', 'per-session', 'per-workspace')
        """
        self.sessions = sessions
        self.mode = mode
    
    def generate(self) -> str:
        """Generate complete HTML document.
        
        Modes:
        - 'single': All sessions in one HTML file (default, fully implemented)
        - 'per-session': One HTML file per session (TODO: requires directory output)
        - 'per-workspace': One HTML file per workspace (TODO: requires directory output)
        
        Note: Currently all modes output single-file format. Multi-file modes require
        CLI refactoring to handle directory output instead of single file.
        
        Returns:
            Complete HTML string with TailwindCSS styling
        """
        # TODO T069-T071: Implement per-session and per-workspace modes
        # For now, all modes use single-file format
        
        html_parts = []
        
        # HTML head with TailwindCSS
        html_parts.append(self._generate_html_head())
        
        # Body start
        html_parts.append('<body class="bg-gray-50 min-h-screen">')

        # Dark mode toggle — fixed top-right
        html_parts.append('''<button id="dm-toggle" onclick="toggleDark()"
    class="fixed top-3 right-4 z-50 px-3 py-1.5 rounded-full text-xs font-medium
           bg-gray-200 text-gray-700 hover:bg-gray-300 shadow transition-colors">
    🌙 Dark
</button>''')

        # Main content container (no header)
        html_parts.append('<main class="container mx-auto px-4 py-8 max-w-5xl">')
        
        # Render all sessions
        for session in self.sessions:
            html_parts.append(self._generate_session_section(session))
        
        # Main container close
        html_parts.append('</main>')
        
        # Body and HTML close
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    def _generate_html_head(self) -> str:
        """Generate HTML head section with TailwindCSS CDN.
        
        Returns:
            HTML head section as string
        """
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat History - VS Code WorkspaceStorage Parser</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>tailwind.config = { darkMode: 'class' }</script>
    <style>
        /* Custom scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* Code block styling */
        pre {
            background: #f6f8fa;
            border-radius: 6px 6px 0 0;
            padding: 12px;
            overflow-x: scroll;
            overflow-y: auto;
            margin: 0;
            /* Prevent the block from blowing out its flex parent */
            min-width: 0;
            max-width: 100%;
            box-sizing: border-box;
            /* ~5 lines: line-height 1.5 * font-size 0.9em * 5 + padding */
            max-height: calc(5 * 1.35em + 24px);
            transition: max-height 0.2s ease;
        }
        pre.expanded {
            max-height: 80vh;
        }
        code {
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }
        .code-toggle {
            display: block;
            width: 100%;
            background: #e8eaed;
            border: none;
            border-radius: 0 0 6px 6px;
            padding: 3px 12px;
            font-size: 0.75em;
            color: #555;
            cursor: pointer;
            text-align: left;
        }
        .code-toggle:hover {
            background: #d0d3d8;
        }

        /* ── VS Code Dark Modern ────────────────────────────────────────────
           Palette reference:
             #1e1e1e  editor background
             #252526  sidebar / panel background
             #2d2d30  input / widget background
             #3e3e42  border
             #cccccc  foreground
             #858585  muted / description text
             #1c3354  chat user-message blue
             #0e639c  button / accent blue
        ──────────────────────────────────────────────────────────────────── */
        .dark body        { background-color: #1e1e1e; }
        .dark .vsc-card   { background-color: #252526; }
        .dark .vsc-divider{ border-color: #3e3e42; }
        .dark .vsc-title  { color: #cccccc; }
        .dark .vsc-meta   { color: #858585; }
        .dark .vsc-bubble-user {
            background-color: #1c3354;
            color: #cccccc;
        }
        .dark .vsc-bubble-assistant {
            background-color: #2d2d30;
            border-color: #3e3e42;
            color: #cccccc;
        }
        .dark pre          { background: #1e1e1e; color: #d4d4d4; }
        .dark .code-toggle { background: #2d2d30; color: #858585; border-top: 1px solid #3e3e42; }
        .dark .code-toggle:hover { background: #3e3e42; }
        .dark .vsc-inline-code {
            background-color: #2d2d30;
            color: #9cdcfe;
        }
        .dark .vsc-file-chip {
            background-color: #1c3354;
            color: #9cdcfe;
            border-color: #0e639c;
        }
        .dark #dm-toggle   { background-color: #3c3c3c; color: #cccccc; }
        .dark #dm-toggle:hover { background-color: #4e4e4e; }
        /* scrollbar */
        .dark ::-webkit-scrollbar-track  { background: #252526; }
        .dark ::-webkit-scrollbar-thumb  { background: #555; }
        .dark ::-webkit-scrollbar-thumb:hover { background: #777; }
    </style>
    <script>
        function toggleCode(btn) {
            var pre = btn.previousElementSibling;
            var expanded = pre.classList.toggle('expanded');
            btn.textContent = expanded ? 'Show less ▲' : 'Show more ▼';
        }
        function toggleDark() {
            var dark = document.documentElement.classList.toggle('dark');
            var btn = document.getElementById('dm-toggle');
            btn.textContent = dark ? '☀️ Light' : '🌙 Dark';
        }
    </script>
</head>'''
    
    def _generate_header(self) -> str:
        """Generate page header with title and metadata.
        
        Returns:
            HTML header section as string
        """
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_count = len(self.sessions)
        total_messages = sum(len(s.messages) for s in self.sessions)
        
        return f'''<header class="bg-white border-b border-gray-200 shadow-sm">
    <div class="container mx-auto px-4 py-6 max-w-5xl">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Chat History</h1>
        <div class="text-sm text-gray-600 space-y-1">
            <p>Generated: {generation_time}</p>
            <p>Sessions: {session_count} | Messages: {total_messages}</p>
        </div>
    </div>
</header>'''
    
    def _generate_session_section(self, session: ChatSession) -> str:
        """Generate HTML for a single chat session.
        
        Args:
            session: ChatSession object to render
            
        Returns:
            HTML section for the session
        """
        parts = []
        
        # Session header
        creation_date = session.creation_date.strftime("%Y-%m-%d %H:%M:%S") if session.creation_date else "Unknown"
        workspace_label = f" (Workspace: {session.workspace_id[:8]}...)" if session.workspace_id else ""
        
        parts.append(f'''<section class="vsc-card mb-12 bg-white rounded-lg shadow-md p-6">
    <div class="vsc-divider border-b border-gray-200 pb-4 mb-6">
        <h2 class="vsc-title text-xl font-semibold text-gray-800">{session.session_id}{workspace_label}</h2>
        <p class="vsc-meta text-sm text-gray-500 mt-1">Created: {creation_date}</p>
        {f'<p class="vsc-meta text-sm text-gray-500">Source: {session.source_file.name}</p>' if session.source_file else ''}
    </div>''')
        
        # Messages in Copilot-style layout
        parts.append('    <div class="space-y-4">')
        
        for message in session.messages:
            if message.role == "user":
                parts.append(self._render_user_message(
                    message,
                    avatar_url=session.requester_avatar_url,
                    username=session.requester_username,
                ))
            elif message.role == "assistant":
                msg_type = self._detect_message_type(message)
                if msg_type == "skip":
                    continue
                elif msg_type == "action":
                    parts.append(self._render_action_note(message))
                elif msg_type == "confirmation":
                    parts.append(self._render_confirmation(message))
                else:
                    parts.append(self._render_assistant_message(
                        message,
                        avatar_url=session.responder_avatar_url,
                        username=session.responder_username,
                        icon_id=session.responder_avatar_icon_id,
                    ))
        
        parts.append('    </div>')  # Close messages container
        
        # Parse errors if any
        if session.parse_errors:
            parts.append(self._render_parse_errors(session.parse_errors))
        
        parts.append('</section>')  # Close session section
        
        return '\n'.join(parts)
    
    # Copilot mascot as an inline SVG (self-contained, no network request needed)
    _COPILOT_SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">'
        '<circle cx="16" cy="16" r="16" fill="#6e40c9"/>'
        # helmet dome
        '<path d="M8 16 C8 10 24 10 24 16 L24 20 C24 22.2 22.2 24 20 24 L12 24'
        ' C9.8 24 8 22.2 8 20 Z" fill="white"/>'
        # eyes (dark cutouts)
        '<circle cx="12.5" cy="17" r="2" fill="#6e40c9"/>'
        '<circle cx="19.5" cy="17" r="2" fill="#6e40c9"/>'
        # visor band
        '<rect x="8" y="19.5" width="16" height="2.5" rx="1" fill="#6e40c9" opacity="0.25"/>'
        '</svg>'
    )

    def _render_avatar(self, avatar_url: str | None, fallback: str, bg_class: str, icon_id: str | None = None) -> str:
        """Render an avatar: image if URL available, known icon if id matches, otherwise a coloured initial circle.

        Args:
            avatar_url: Optional image URL
            fallback: Single character / emoji shown when no URL is available
            bg_class: Tailwind background colour class for the fallback circle
            icon_id: Optional VS Code icon id (e.g. 'copilot')

        Returns:
            HTML for the avatar element
        """
        if avatar_url:
            escaped_url = self._escape_html(avatar_url)
            return (
                f'<img src="{escaped_url}" alt="avatar" '
                f'class="flex-shrink-0 w-8 h-8 rounded-full object-cover">'
            )
        if icon_id == "copilot":
            return f'<div class="flex-shrink-0 w-8 h-8 rounded-full overflow-hidden">{self._COPILOT_SVG}</div>'
        return (
            f'<div class="flex-shrink-0 w-8 h-8 rounded-full {bg_class} '
            f'flex items-center justify-center text-white text-sm font-medium">'
            f'{fallback}</div>'
        )

    def _render_user_message(self, message: Message, avatar_url: str | None = None, username: str | None = None) -> str:
        """Render a user message (right-aligned, blue background).

        Args:
            message: Message object with role='user'
            avatar_url: Optional avatar image URL
            username: Optional display name

        Returns:
            HTML for user message
        """
        timestamp = message.timestamp.strftime("%H:%M:%S") if message.timestamp else ""
        content = self._format_markdown(message.content)
        fallback = (username[0].upper() if username else "U")
        avatar = self._render_avatar(avatar_url, fallback, "bg-blue-500")

        return f'''        <div class="flex justify-end">
            <div class="max-w-3xl">
                <div class="flex items-start gap-3 flex-row-reverse">
                    {avatar}
                    <div class="flex-1 min-w-0">
                        <div class="vsc-bubble-user bg-blue-100 rounded-2xl rounded-tr-sm px-4 py-3 text-gray-900">
                            {content}
                        </div>
                        <div class="text-xs text-gray-500 mt-1 text-right">{timestamp}</div>
                    </div>
                </div>
            </div>
        </div>'''
    
    def _render_assistant_message(self, message: Message, avatar_url: str | None = None, username: str | None = None, icon_id: str | None = None) -> str:
        """Render an assistant message (left-aligned, white background with border).

        Args:
            message: Message object with role='assistant'
            avatar_url: Optional avatar image URL
            username: Optional display name

        Returns:
            HTML for assistant message
        """
        timestamp = message.timestamp.strftime("%H:%M:%S") if message.timestamp else ""
        content = self._format_markdown(message.content)
        fallback = (username[0].upper() if username else "A")
        avatar = self._render_avatar(avatar_url, fallback, "bg-purple-500", icon_id=icon_id)

        return f'''        <div class="flex justify-start">
            <div class="max-w-3xl">
                <div class="flex items-start gap-3">
                    {avatar}
                    <div class="flex-1 min-w-0">
                        <div class="vsc-bubble-assistant bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 text-gray-900 shadow-sm">
                            {content}
                        </div>
                        <div class="text-xs text-gray-500 mt-1">{timestamp}</div>
                    </div>
                </div>
            </div>
        </div>'''

    def _file_chip(self, filename: str) -> str:
        """Render a filename as a small inline badge."""
        # Handle both forward-slash and backslash paths
        name = filename.rstrip('/\\').replace('\\', '/').rsplit('/', 1)[-1]
        return (
            f'<span class="vsc-file-chip inline-flex items-center gap-1 px-2 py-0.5 rounded '
            f'text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">'
            f'<span>📄</span>{name}</span>'
        )

    def _render_action_note(self, message: Message) -> str:
        """Render a tool/action as a compact inline note with no chat bubble.

        File paths are shortened to just the filename to avoid leaking full
        local paths into the output.

        Returns:
            HTML for a slim, non-bubble action indicator aligned with bubbles.
        """
        import re
        content = self._shorten_paths(message.content).strip().strip('[]')
        # Drop the redundant "Tool: " prefix — ⚙ already marks this as a tool action
        content = re.sub(r'^Tool:\s*', '', content, flags=re.IGNORECASE)
        content = self._escape_html(content)
        # Convert [](filename) left over from URI shortening into file chips
        content = re.sub(r'\[\]\(([^)]+)\)', lambda m: self._file_chip(m.group(1)), content)
        return f'        <div class="pl-11 py-0.5 text-xs text-gray-400 italic">⚙ {content}</div>'

    def _render_confirmation(self, message: Message) -> str:
        """Render a confirmation/continue prompt as a distinct amber callout."""
        import re
        content = message.content.strip()
        # Extract title and body from [Confirmation: title]\nbody
        m = re.match(r'^\[Confirmation:\s*(.*?)\]\s*\n?(.*)', content, re.DOTALL)
        if m:
            title = self._escape_html(m.group(1).strip())
            body = self._escape_html(m.group(2).strip())
        else:
            title = self._escape_html(content.lstrip('[').split(']')[0].replace('Confirmation:', '').strip())
            body = ""
        body_html = f'<p class="text-sm text-amber-700 mt-1">{body}</p>' if body else ""
        return (
            f'        <div class="pl-11 py-2">'
            f'<div class="inline-block rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-amber-800">'
            f'<span class="font-semibold">❓ {title}</span>'
            f'{body_html}'
            f'</div></div>'
        )

    def _shorten_paths(self, text: str) -> str:
        """Replace absolute file paths with just the filename.

        Handles:
        - Plain paths: /home/user/.../File.php
        - file:// URIs: file:///home/user/.../File.php (with optional #fragment)
        - Backslash paths: \\home\\user\\...\\File.go (Windows/WSL paths in JSON)
        """
        import re

        def basename_from_uri(m: re.Match) -> str:
            # Strip fragment, then take everything after the last /
            path = m.group(0).split('#')[0]
            return path.rstrip('/').rsplit('/', 1)[-1]

        def basename_from_path(m: re.Match) -> str:
            return m.group(0).rsplit('/', 1)[-1]

        def basename_from_backslash_path(m: re.Match) -> str:
            return m.group(0).rsplit('\\', 1)[-1]

        # file:// URIs (consume optional #fragment so it doesn't leak)
        text = re.sub(r'file://[^\s)\]#,]+(#[^\s)\]]*)?', basename_from_uri, text)
        # Bare absolute paths: must contain at least one / separator after root
        text = re.sub(r'/(?:[^\s,\[\]()\'"]+/)+[^\s,\[\]()\'"#/]+', basename_from_path, text)
        # Backslash paths: \\seg\\seg\\...\\filename (at least two segments)
        text = re.sub(r'\\(?:[^\s,\[\]()\'"\\]+\\)+[^\s,\[\]()\'"\\]+', basename_from_backslash_path, text)
        return text
    
    def _detect_message_type(self, message: Message) -> str:
        """Detect if a message is a regular response or an action/tool invocation.
        
        Args:
            message: Message object to analyze
            
        Returns:
            'action' if message is a tool/action, 'text' otherwise
        """
        # A message is an action only if it IS one — i.e. it starts with a marker.
        # Using `in` would misclassify real text that has a [File: ...] reference appended.
        content_lower = message.content.strip().lower()

        if content_lower.startswith(('[tool:', '[thinking]', '[action:', '[editing:', '[referencing:')):
            return "action"

        if content_lower.startswith('[confirmation:'):
            return "confirmation"

        if content_lower.startswith('[mcpservers'):
            return "skip"

        return "text"
    
    def _render_parse_errors(self, errors: list[str]) -> str:
        """Render parse errors section.
        
        Args:
            errors: List of error messages
            
        Returns:
            HTML for error display
        """
        error_items = '\n'.join(f'            <li class="text-sm">{self._escape_html(err)}</li>' for err in errors)
        
        return f'''    <div class="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 class="text-sm font-semibold text-yellow-800 mb-2">⚠️ Parse Warnings</h3>
        <ul class="list-disc list-inside text-yellow-700">
{error_items}
        </ul>
    </div>'''
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters.
        
        Args:
            text: Raw text string
            
        Returns:
            HTML-escaped string
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
    
    def _format_markdown(self, text: str) -> str:
        """Render markdown to HTML using markdown-it-py.

        File chip markers and VS Code file references are substituted before
        markdown parsing so they survive as raw HTML.
        """
        import re

        # --- pre-processing: replace file/path markers with HTML chips ---
        # These markers contain paths that must not be touched by the markdown parser.
        file_chip = self._file_chip

        text = re.sub(r'\[File: ([^\]]+)\]', lambda m: file_chip(m.group(1)), text)
        text = re.sub(r'\[File Edit: ([^\]]+)\]', lambda m: file_chip(m.group(1)), text)
        text = re.sub(r'\[\]\(([^)]+)\)', lambda m: file_chip(m.group(1)), text)
        text = re.sub(r'#file:(\S+)', lambda m: file_chip(m.group(1)), text)

        # --- markdown rendering ---
        md = MarkdownIt("commonmark", {"html": True})
        html = md.render(text)

        # --- post-processing: style elements to match Tailwind design ---
        # Code blocks: add language class and collapse toggle
        def style_pre(m: re.Match) -> str:
            lang_attr = m.group(1)
            code_body = m.group(2)
            # Always emit <code> with at least one attribute so it won't match
            # the bare <code> inline-code replacement below.
            code_tag = f'<code class="vsc-block-code"{lang_attr}>' if not lang_attr else f'<code{lang_attr}>'
            return (
                f'<pre class="vsc-code-block bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto my-2 text-sm">'
                f'{code_tag}{code_body}</code></pre>'
                f'<button class="code-toggle" onclick="toggleCode(this)">Show more ▼</button>'
            )

        html = re.sub(
            r'<pre><code([^>]*)>(.*?)</code></pre>',
            style_pre,
            html,
            flags=re.DOTALL,
        )

        # Inline code — only bare <code> (no attributes), so block code is not affected
        html = re.sub(
            r'<code>',
            '<code class="vsc-inline-code bg-gray-200 dark:bg-gray-700 px-1 rounded text-sm">',
            html,
        )

        # Headings
        for level in range(1, 7):
            sizes = {1: 'text-xl', 2: 'text-lg', 3: 'text-base', 4: 'text-sm', 5: 'text-sm', 6: 'text-xs'}
            html = html.replace(f'<h{level}>', f'<h{level} class="font-bold {sizes[level]} mt-3 mb-1">')

        # Lists
        html = html.replace('<ul>', '<ul class="list-disc list-inside my-1 space-y-0.5">')
        html = html.replace('<ol>', '<ol class="list-decimal list-inside my-1 space-y-0.5">')

        # Blockquotes
        html = html.replace('<blockquote>', '<blockquote class="border-l-4 border-gray-300 pl-3 italic text-gray-600 my-2">')

        # Paragraphs — skip adding margin if this is a single-paragraph response
        # (avoid double-spacing short answers)
        if html.count('<p>') > 1:
            html = html.replace('<p>', '<p class="my-1">')

        # Links
        html = re.sub(r'<a href="', '<a class="text-blue-600 underline" href="', html)

        return html

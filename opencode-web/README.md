# OpenCode Web Client

A standalone, modern web interface for your local OpenCode agent server.

## Features

- **No Project Cloning Required**: Connects directly to any running OpenCode instance via REST & SSE APIs.
- **Real-Time Token Streaming**: Server-Sent Events (`message.part.delta`) support with instantaneous typing animation.
- **Markdown & Syntax Highlighting**: Full GitHub Flavored Markdown rendering with syntax highlighting and one-click code copy.
- **Thinking / Reasoning Collapsible**: Displays internal model reasoning blocks in clean toggles.
- **Session History & Management**: Create new chats, switch between previous sessions, or delete them.
- **Theme Support**: Seamless Dark / Light mode toggle.
- **Zero External Dependencies**: Python runner requires no `pip install` (runs with Python standard library).

---

## Quick Start

### 1. Ensure OpenCode is Running
In one terminal, make sure your OpenCode server is active:
```bash
opencode serve --port 4096
# Or if you used web:
opencode web
```

### 2. Launch the Web Client
In another terminal, navigate to this folder and start the client:
```bash
cd opencode-web
./run.sh
```
*(Or directly: `python3 server.py --port 3000`)*

### 3. Open in Browser
Visit **`http://localhost:3000`** (or open `index.html` directly in your browser).

---

## How It Works

```
Browser (UI)  ──►  POST /session                 (Initialize / get session ID)
              ──►  POST /session/{id}/message    (Send user prompt)
              ◄──  GET  /event                   (Stream token deltas via SSE)
              ◄──  HTTP 200 Response             (Final synchronized reply)
```

- **Default Backend URL:** `http://127.0.0.1:4096`
- **Settings:** You can change the backend URL directly from the settings gear icon (⚙️) inside the UI at any time.

# AI Environment Agent

Local AI agent platform — a FastAPI backend with Azure OpenAI, workspace file tools, and a web chat UI. Supports single-turn **Chat** mode and multi-step **Cowork** mode (outcome-oriented autonomous tasks).
**Repository:** [github.com/thanakornboonsaard-cmyk/AI-Env-System](https://github.com/thanakornboonsaard-cmyk/AI-Env-System)

---

## Features

| Feature | Description |
|---------|-------------|
| **Chat mode** | One action per message — plan, tool, summarize |
| **Cowork mode** | Multi-step autonomous loop (up to 8 steps) with live SSE progress |
| **Workspace tools** | List, read, create, delete files; write notes; run Python scripts |
| **Session upload** | Attach one file per session (100 MB max) — text, PDF, and more |
| **Delete confirmation** | Destructive deletes require explicit user approval |
| **Python run canvas** | Inline + side panel for stdout/stderr after script execution |
| **PDF reading** | Extract text from PDF uploads via `pypdf` |
| **Token tracking** | Per-request and session token usage in the UI |
| **MCP server** | Stdio MCP server for Cursor (`list_workspace_files`, `read_workspace_file`, `health`) |
| **Workspace browser** | Sidebar file list with one-click prompts |

---

## Requirements

- Python 3.11+ (3.12 recommended)
- Azure OpenAI endpoint and API key
- Windows, macOS, or Linux

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/thanakornboonsaard-cmyk/AI-Env-System.git
cd AI-Env-System

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_MODEL=gpt-5.1-codex-mini
```

> **Never commit `.env`.** It is listed in `.gitignore`.

### 3. Run the server

```bash
python -m uvicorn main:app --reload --port 8000
```

Open in browser:

- **Chat UI:** http://localhost:8000/chat
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

---

## Usage

### Chat mode

Ask questions or request a single action:

- *"มีไฟล์อะไรใน workspace บ้าง"*
- *"อ่านไฟล์ project.txt แล้วสรุปให้หน่อย"*
- *"สร้างไฟล์ report.txt ด้วยเนื้อหา Hello"*

### Cowork mode

Switch to **Cowork** in the top bar, then describe a **goal** (not just a question). The agent plans and executes multiple steps, streaming progress in real time:

- *"อ่านไฟล์ project.txt แล้วสรุปเป็น bullet points ภาษาไทย"*
- *"List all workspace files and write a summary note"*

Cowork stops early if a step needs delete confirmation.

### Attach a file

Use the 📎 button in the composer or drag-and-drop a file (max 1 file, 100 MB per session). Ask about the attached file in Thai or English.

### Run Python

Ask the agent to write and run a script:

- *"เขียน Python Hello World แล้วรันให้ดู"*

Scripts are saved under `workspace/scripts/` and executed with the project virtualenv.

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/agent/chat` | Chat agent (`mode`: `chat` or `cowork`) |
| `POST` | `/agent/cowork` | Cowork task with SSE progress stream |
| `POST` | `/agent/confirm` | Confirm or cancel pending delete |
| `POST` | `/sessions/{id}/upload` | Upload session file |
| `GET` | `/sessions/{id}/upload` | Get current upload metadata |
| `DELETE` | `/sessions/{id}/upload` | Remove session upload |
| `GET` | `/sessions/{id}/messages` | Session message history |
| `GET` | `/sessions/{id}/usage` | Token usage for session |
| `GET` | `/workspace/files` | List workspace files |
| `GET` | `/workspace/file?path=...` | Read a workspace file |
| `POST` | `/files/create` | Create file directly (no agent) |
| `GET` | `/health` | Health check |

### Example: Chat request

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "demo-session", "mode": "chat"}'
```

### Example: Cowork request (SSE)

```bash
curl -N -X POST http://localhost:8000/agent/cowork \
  -H "Content-Type: application/json" \
  -d '{"goal": "List workspace files and summarize project.txt", "session_id": "demo-session"}'
```

---

## Project Structure

```
├── main.py                 # Uvicorn entry point
├── run_mcp_server.py       # MCP stdio server launcher
├── requirements.txt
├── app/
│   ├── main.py             # FastAPI app
│   ├── core/               # Config, Azure client, token usage
│   ├── memory/             # In-memory session store
│   ├── runtime/            # Agent, Cowork, planner, confirmations
│   ├── tools/              # File tools, PDF reader, Python runner
│   ├── routes/             # HTTP routes
│   └── mcp/                # MCP workspace server
├── frontend/               # chat.html, app.js, style.css
├── workspace/              # Agent sandbox (notes, scripts, uploads)
│   ├── notes/
│   ├── scripts/
│   └── sessions/
└── test_*.py               # Smoke and unit tests
```

---

## MCP (Cursor Integration)

The project includes an MCP server exposing workspace tools over stdio.

**Run manually:**

```bash
python run_mcp_server.py
```

**Cursor config** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "workspace-server": {
      "command": ".venv/Scripts/python.exe",
      "args": ["run_mcp_server.py"]
    }
  }
}
```

On macOS/Linux, change the command path to `.venv/bin/python`.

**Test MCP:**

```bash
python test_mcp.py
```

---

## Testing

```bash
python test_endpoints.py
python test_cowork.py
python test_mcp.py
python test_session_upload.py
python test_pdf_read.py
```

---

## Workspace Layout

| Path | Purpose |
|------|---------|
| `workspace/project.txt` | Sample project context file |
| `workspace/notes/` | User-created text files |
| `workspace/scripts/` | Python scripts created by the agent |
| `workspace/sessions/{id}/upload/` | Per-session file uploads |

Protected files (cannot be deleted by agent): `.env`, `project.txt`

---

## Architecture

```
Browser (chat.html)
    │
    ▼
FastAPI routes
    │
    ├── Chat  → planner → single tool → summarize
    │
    └── Cowork → loop (plan → tool → summarize) → SSE events → final deliverable
                        │
                        ▼
                 workspace/ tools + Azure OpenAI
```

- **Planner** chooses one action per step (JSON).
- **Runtime** executes tools and handles delete confirmation flow.
- **Sessions** are in-memory; session ID persists in browser `localStorage`.
- **Uploads** and workspace files persist on disk.

---

## Security Notes

- API keys live only in `.env` (not committed).
- File operations are sandboxed to `workspace/`.
- Delete requires user confirmation.
- Python execution uses a 15-second timeout and the project venv.
- Do not expose this server to the public internet without authentication.

---

## License

Internal project. Contact the repository owner for usage terms.

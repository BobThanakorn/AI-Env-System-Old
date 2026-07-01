Project: TCC AI Environment Agent

Context:
This project is an MVP of a local AI Environment / Agent Runtime inspired by systems like OpenClaw, IronClaw, Cursor, and Google Notebook-style interfaces. The current goal is to build a local 24/7 AI agent environment that runs on the user's machine, uses Azure AI through the OpenAI-compatible SDK, and gradually evolves into a secure AI Agent Runtime with tools, workspace, memory, policy, audit log, and UI.

Current project directory:
C:\Users\Thanakorn Boonsa-ard\Downloads\TCC Project

Current structure:
TCC Project/
├── .venv/
├── .env
├── PROJECT_CONTEXT.md
├── main.py
├── requirements.txt
├── frontend/
│   ├── chat.html
│   ├── style.css
│   └── app.js
└── workspace/
    ├── project.txt
    └── notes/

Current tech stack:
- Python
- FastAPI
- Uvicorn
- OpenAI Python SDK
- Azure AI Foundry / Azure OpenAI compatible endpoint
- python-dotenv
- Static HTML/CSS/JS frontend
- Local workspace tools

Current .env variables:
AZURE_OPENAI_BASE_URL=https://ai-environment-resource.services.ai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=<user secret key, do not expose>
AZURE_OPENAI_MODEL=gpt-5.1-codex-mini

Current requirements.txt:
fastapi
uvicorn[standard]
openai
python-dotenv
pydantic

Current run command:
python -m uvicorn main:app --reload --port 8000

Main URLs:
- Chat UI: http://localhost:8000/chat
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Debug env: http://localhost:8000/debug/env
- Debug frontend: http://localhost:8000/debug/frontend
- Agent API: POST http://localhost:8000/agent/chat

Current status:
- FastAPI server works.
- /health works.
- .env loading works.
- Azure AI connection works.
- /agent/chat works.
- Basic chatbot UI works at /chat.
- Frontend is separated into frontend/chat.html, frontend/style.css, frontend/app.js.
- The project can answer in English and Thai.
- The agent can choose between a direct answer and simple local tools.

Current implemented agent actions:
1. answer
   - Not a local tool.
   - Used when the user asks a general question.
   - Flow: user message -> Azure AI -> final answer.

2. list_files
   - Local executable tool.
   - Lists files inside workspace/.
   - Used when the user asks what files are available.

3. read_file
   - Local executable tool.
   - Reads a file inside workspace/.
   - Uses safe_path() to prevent reading files outside workspace.
   - Content is truncated to first 8000 characters.

4. write_note
   - Local executable tool.
   - Writes a markdown note into workspace/notes/.
   - Filename format: note_YYYYMMDD_HHMMSS.md

Important current backend behavior:
- main.py loads .env from BASE_DIR / ".env" using load_dotenv(ENV_PATH, override=True).
- Azure AI is called through OpenAI SDK using get_client().
- The project uses the OpenAI-compatible Responses API:
  client.responses.create(...)
- There is retry behavior planned or implemented for reasoning support:
  First try with reasoning={"effort": "medium"}.
  If unsupported, retry without reasoning.
- Do not use Chat Completions for this deployment unless verified. Earlier chat.completions.create returned:
  "The requested operation is unsupported."
- The Responses API path works better for the current Azure model.

Current backend pipeline:
User
-> Browser Chat UI at /chat
-> frontend/app.js sends POST /agent/chat
-> FastAPI receives AgentRequest(message)
-> run_agent(message)
-> create_plan(message)
-> Azure AI returns JSON plan
-> extract_json(plan)
-> if action == answer:
      answer_directly(message)
   else:
      execute_tool(action, args)
      summarize_tool_result(message, plan, tool_result)
-> return JSON response to browser
-> frontend renders answer and optional raw details

Current Mermaid diagram:
flowchart LR
    U[User] --> UI[Chatbot UI /chat]
    UI -->|POST /agent/chat| API[FastAPI Backend]
    API --> RT[Agent Runtime]
    RT --> PLANNER[Planner]
    PLANNER --> AZURE[Azure AI Responses API]
    AZURE --> PLAN[Agent Plan]
    PLAN --> ROUTER[Tool Router]
    ROUTER -->|answer| DIRECT[Direct Answer]
    ROUTER -->|list_files| TOOL1[List Files Tool]
    ROUTER -->|read_file| TOOL2[Read File Tool]
    ROUTER -->|write_note| TOOL3[Write Note Tool]
    TOOL1 --> SUMMARY[Summarize Tool Result]
    TOOL2 --> SUMMARY
    TOOL3 --> SUMMARY
    SUMMARY --> AZURE2[Azure AI Final Response]
    DIRECT --> AZURE2
    AZURE2 --> RESPONSE[Final Answer]
    RESPONSE --> API
    API --> UI
    UI --> U

Current frontend:
- chat.html provides the basic chatbot layout.
- style.css provides a dark UI.
- app.js handles:
  - setPrompt(text)
  - addMessage(role, content, raw)
  - sendMessage()
  - Enter to send, Shift+Enter for newline
- app.js calls:
  fetch("/agent/chat", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ message }) })

Known troubleshooting already solved:
1. Attribute "app" not found
   - Cause: main.py missing app or server reading old file.
   - Fixed by defining app = FastAPI(...).

2. Missing credentials
   - Cause: .env variable names were wrong or not loaded.
   - Correct variable names:
     AZURE_OPENAI_BASE_URL
     AZURE_OPENAI_API_KEY
     AZURE_OPENAI_MODEL

3. Chat Completions unsupported
   - Cause: deployment does not support chat.completions.create.
   - Fixed by using client.responses.create.

4. /chat blank page
   - Cause: frontend/chat.html was empty or server read old frontend file.
   - Fixed by separating frontend files and using HTMLResponse for /chat.

5. PowerShell URL issue
   - Do not type raw URLs directly in PowerShell.
   - Use browser or:
     irm "http://localhost:8000/debug/env"

PowerShell commands used:
Activate venv:
.\.venv\Scripts\Activate.ps1

Run server:
python -m uvicorn main:app --reload --port 8000

Test API:
$body = '{"message":"Hello, what can you do?"}'
Invoke-RestMethod -Uri "http://localhost:8000/agent/chat" -Method POST -ContentType "application/json" -Body $body

Debug env:
irm "http://localhost:8000/debug/env"

Debug frontend:
irm "http://localhost:8000/debug/frontend"

Clear Python cache:
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Current goal:
Continue improving this MVP from a simple chatbot into a real local AI Agent Environment.

Next tasks to implement:

Task 1: Refactor project structure
Current main.py is too large. Split it into modules:
backend/
or app/
├── main.py
├── core/
│   ├── config.py
│   └── azure_client.py
├── runtime/
│   ├── agent_runtime.py
│   ├── planner.py
│   └── parser.py
├── tools/
│   ├── file_tools.py
│   └── note_tools.py
├── audit/
│   └── audit_logger.py
└── routes/
    ├── chat_routes.py
    ├── debug_routes.py
    └── frontend_routes.py

Keep the current behavior working while refactoring.

Task 2: Add audit log
Add an audit log system that records every agent run.

For every request, log:
- timestamp
- user_message
- plan
- selected_action
- tool_args
- tool_result
- final_answer
- status
- error if any

MVP storage:
workspace/audit_logs/audit_YYYYMMDD.jsonl

Each line should be JSON.

Example audit record:
{
  "timestamp": "2026-07-01T12:30:00",
  "user_message": "อ่านไฟล์ project.txt แล้วสรุปให้หน่อย",
  "plan": {...},
  "action": "read_file",
  "args": {"path": "project.txt"},
  "tool_result": {...},
  "answer": "...",
  "status": "success"
}

Task 3: Add more tools
Add these tools:

A. get_workspace_tree
- Return folder tree structure of workspace.

B. create_file
- Create a file inside workspace.
- Args:
  {"path": "example.md", "content": "..."}
- Must use safe_path.

C. append_file
- Append content to existing file.
- Args:
  {"path": "example.md", "content": "..."}

D. search_files
- Search keyword in workspace text files.
- Args:
  {"query": "keyword"}

E. delete_file
- Do not implement direct delete yet.
- Instead return approval_required because deletion should require human approval in the future.

Task 4: Improve planner prompt
Update available actions in the planner prompt to include new tools.
The planner must return only JSON.
Need robust parsing fallback.

Task 5: Add basic policy layer
Before execute_tool(), add check_policy(action, args).

Initial policy:
- Block reading files outside workspace.
- Block reading .env.
- Block reading files with names:
  .env
  id_rsa
  credentials.json
  secret.json
- Block delete_file for now.
- Allow list_files, read_file, write_note, create_file, append_file, search_files.
- High-risk actions should return:
  {"policy": "blocked", "reason": "..."}

Task 6: Improve frontend UI
Make the chat UI more like Cursor/OpenClaw:
- Left sidebar:
  - Workspace
  - Tools
  - Audit
  - Settings
- Center:
  - Chat messages
- Right panel:
  - Agent plan
  - Tool result
  - Raw JSON
- Bottom:
  - Status / logs
Keep it simple, static HTML/CSS/JS for now.

Task 7: Add frontend display for agent details
Current app.js already supports details.
Improve it to show:
- type
- plan.action
- plan.reason
- tool_result.tool
- created file if write_note
- errors

Task 8: Add /audit endpoint
Add:
GET /audit/recent
Return last 20 audit logs.

Add:
GET /audit/file
Return audit log file path or content.

Task 9: Add /workspace endpoint
Add:
GET /workspace/files
Return list_files().

Add:
GET /workspace/read?path=project.txt
Return read_file(path).

Task 10: Prepare for Docker Compose later
Do not implement Docker yet unless asked.
But keep code compatible with Docker:
- Use env vars.
- Use relative folders.
- Do not hardcode Windows-only paths.
- Avoid local absolute paths except debug output.

Important design constraints:
- Do not use local LLM.
- AI model must be called through Azure AI / OpenAI-compatible SDK.
- Keep the app runnable locally.
- Do not put API key in frontend.
- Do not expose .env content.
- Keep all file operations inside workspace/.
- Prioritize simple working MVP over complex architecture.

Recommended immediate next step:
Implement Task 2 first: audit log.
Then Task 3: add more tools.
Then Task 5: policy layer.
Then improve UI.

Expected final MVP after next phase:
A local AI Agent Environment with:
- Chat UI
- Azure AI model
- Agent planner
- Tool router
- Workspace file tools
- Audit log
- Basic policy checks
- Debug endpoints
- Simple UI for plan/tool/audit visibility

Please continue from the existing code without breaking current working behavior.
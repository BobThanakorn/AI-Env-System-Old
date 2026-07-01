# Deep Dive: Complete TCC AI Environment Agent Roadmap

---

## Overview

9 main phases + 3 stretch goals to transform from MVP chatbot → production-ready secure AI agent runtime.

```
Phase 0: Git & Deps           ✅ DONE
Phase 1: Refactor             ✅ DONE
    ↓
Phase 2: Policy Layer         ← Adds guardrails
Phase 3: Audit Logs           ← Adds transparency
Phase 4: Expand Tools         ← Adds capability
Phase 5: Memory               ← Adds context
Phase 6: API Surface          ← Adds endpoints
Phase 7: UI Upgrade           ← Adds UX
Phase 8: Testing              ← Adds reliability
Phase 9: Containerization     ← Adds portability
    ↓
Stretch: 24/7 Tasks, Multi-user, Integrations
```

---

# PHASE 0: Git & Dependencies ✅ (COMPLETED)

## Objectives
- Initialize version control safely (don't expose `.env` or `venv`)
- Lock dependency versions for reproducibility

## What Was Done
- ✅ `.gitignore` with Python/venv/IDE/workspace patterns
- ✅ `requirements.txt` with pinned versions
- ✅ Git repo initialized locally

## Success Criteria
- ✅ Can run `git status` without exposing secrets
- ✅ `pip install -r requirements.txt` in a fresh venv works identically

## Why It Matters
- **Reproducibility**: Any developer/server uses exact same dependency versions
- **Security**: Secrets never accidentally committed
- **Collaboration**: Clean history ready for team handoff

---

# PHASE 1: Refactor ✅ (COMPLETED)

## Objectives
- Split 450-line `main.py` into 11 focused modules
- Enable independent testing of components
- Prepare for policy/audit/memory layers

## What Was Done
- ✅ `app/core/config.py` — Configuration & paths
- ✅ `app/core/azure_client.py` — Azure API wrapper
- ✅ `app/runtime/parser.py` — JSON extraction logic
- ✅ `app/runtime/planner.py` — Planning & answering
- ✅ `app/tools/file_tools.py` — Workspace tool dispatcher
- ✅ `app/runtime/agent_runtime.py` — Agent orchestration
- ✅ `app/routes/utils.py` — Route handler helpers
- ✅ `app/routes/frontend_routes.py` — Frontend endpoints
- ✅ `app/routes/chat_routes.py` — Agent chat endpoint
- ✅ `app/main.py` — FastAPI app factory
- ✅ Root `main.py` — Entry point wrapper

## Module Dependency Graph

```
main.py (root)
    ↓
app/main.py
    ├─ app/core/config.py
    ├─ app/routes/frontend_routes.py
    │   └─ app/routes/utils.py
    │       └─ app/core/config.py
    └─ app/routes/chat_routes.py
        └─ app/runtime/agent_runtime.py
            ├─ app/runtime/planner.py
            │   ├─ app/core/azure_client.py
            │   │   └─ app/core/config.py
            │   └─ app/runtime/parser.py
            └─ app/tools/file_tools.py
                └─ app/core/config.py
```

## Success Criteria
- ✅ `python validate_refactor.py` shows all imports work
- ✅ `python main.py` starts server on port 8000
- ✅ All endpoints work identically to before
- ✅ No breaking changes

## Why It Matters
- **Maintainability**: 70–80 lines per module vs. 450 in one
- **Testability**: Can test planner independently, tools independently
- **Extensibility**: Adding policy/audit/memory layers is now straightforward
- **Onboarding**: New developers understand the structure immediately

---

# PHASE 2: Policy Layer (GUARDRAILS)

## Objectives
- Implement security checks before tool execution
- Block unsafe operations (delete, path escape, sensitive files)
- Return structured approval-required responses

## What Gets Built

### New Files
- `app/core/policy.py` — Policy enforcement engine

### Code Example

```python
# app/core/policy.py

from enum import Enum
from typing import Any

class PolicyAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    APPROVAL_REQUIRED = "approval_required"

class PolicyDecision:
    def __init__(self, action: PolicyAction, reason: str = ""):
        self.action = action
        self.reason = reason

def check_policy(tool_action: str, args: dict[str, Any]) -> PolicyDecision:
    """Check if action is allowed by policy."""
    
    # Blocked file names
    blocked_files = {".env", "id_rsa", "credentials.json", "secret.json"}
    
    # Block any delete operations for now
    if tool_action == "delete_file":
        return PolicyDecision(
            PolicyAction.APPROVAL_REQUIRED,
            "Delete operations require human approval"
        )
    
    # Block .env reads
    if tool_action == "read_file":
        path = args.get("path", "").lower()
        if path == ".env" or path.endswith("/.env"):
            return PolicyDecision(
                PolicyAction.BLOCK,
                "Cannot read .env file (contains secrets)"
            )
        
        if any(blocked in path for blocked in blocked_files):
            return PolicyDecision(
                PolicyAction.BLOCK,
                f"Cannot read sensitive file: {path}"
            )
    
    # Allow safe operations
    if tool_action in ["list_files", "read_file", "write_note", 
                       "create_file", "append_file", "search_files"]:
        return PolicyDecision(PolicyAction.ALLOW)
    
    # Default: unknown action blocks
    return PolicyDecision(
        PolicyAction.BLOCK,
        f"Unknown action: {tool_action}"
    )
```

### Changes to `app/tools/file_tools.py`

```python
# Before
def execute_tool(action: str, args: dict[str, Any]) -> dict[str, Any]:
    if action == "list_files":
        return list_files()
    ...

# After
def execute_tool(action: str, args: dict[str, Any]) -> dict[str, Any]:
    from app.core.policy import check_policy
    
    decision = check_policy(action, args)
    
    if decision.action == PolicyAction.BLOCK:
        return {
            "tool": action,
            "status": "blocked",
            "reason": decision.reason,
        }
    
    if decision.action == PolicyAction.APPROVAL_REQUIRED:
        return {
            "tool": action,
            "status": "approval_required",
            "reason": decision.reason,
        }
    
    # Action is allowed
    if action == "list_files":
        return list_files()
    ...
```

## Policies Implemented

| Action | Policy |
|--------|--------|
| `list_files` | ALLOW |
| `read_file` (safe paths) | ALLOW |
| `read_file` (.env, secrets) | BLOCK |
| `write_note` | ALLOW |
| `create_file` | ALLOW |
| `append_file` | ALLOW |
| `search_files` | ALLOW |
| `delete_file` | APPROVAL_REQUIRED |
| Unknown actions | BLOCK |

## Success Criteria
- ✅ Trying to read `.env` returns `{"status": "blocked", "reason": "..."}`
- ✅ Trying to delete a file returns `{"status": "approval_required"}`
- ✅ Safe operations still work
- ✅ Policy decisions are logged (Phase 3)

## Testing Scenarios
```python
# Should block
check_policy("read_file", {"path": ".env"})
  → PolicyDecision(BLOCK, "Cannot read .env file")

# Should require approval
check_policy("delete_file", {"path": "project.txt"})
  → PolicyDecision(APPROVAL_REQUIRED, "Delete operations require human approval")

# Should allow
check_policy("read_file", {"path": "project.txt"})
  → PolicyDecision(ALLOW, "")
```

## Why It Matters
- **Security**: Prevents accidental or malicious data leaks
- **Trust**: Users know the agent won't escape the sandbox
- **Audit**: All policy violations are logged
- **Foundation**: Required before adding approval workflows

## Effort Estimate
- **~2 hours**: Write policy.py, integrate into file_tools.py, test

---

# PHASE 3: Audit Logs (TRANSPARENCY)

## Objectives
- Log every agent action (request, plan, decision, result)
- Persist to local JSONL files (one per day)
- Enable audit queries (recent, by date, by action)

## What Gets Built

### New Files
- `app/audit/audit_logger.py` — Audit logging engine
- Audit storage: `workspace/audit_logs/audit_YYYYMMDD.jsonl`

### Code Example

```python
# app/audit/audit_logger.py

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import AUDIT_LOG_DIR

class AuditLogger:
    @staticmethod
    def log_agent_run(
        user_message: str,
        plan: dict[str, Any],
        action: str,
        args: dict[str, Any],
        tool_result: dict[str, Any] | None,
        final_answer: str,
        status: str = "success",
        error: str | None = None,
    ) -> None:
        """Log a complete agent run."""
        
        timestamp = datetime.utcnow().isoformat()
        date_key = datetime.utcnow().strftime("%Y%m%d")
        
        record = {
            "timestamp": timestamp,
            "user_message": user_message[:500],  # Truncate very long messages
            "plan": plan,
            "action": action,
            "args": args,
            "tool_result": tool_result,
            "final_answer": final_answer[:500],  # Truncate answer
            "status": status,
            "error": error,
        }
        
        # Write to daily JSONL file
        log_file = AUDIT_LOG_DIR / f"audit_{date_key}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    @staticmethod
    def read_recent(count: int = 20) -> list[dict[str, Any]]:
        """Read last N audit records from today's file."""
        
        date_key = datetime.utcnow().strftime("%Y%m%d")
        log_file = AUDIT_LOG_DIR / f"audit_{date_key}.jsonl"
        
        if not log_file.exists():
            return []
        
        records = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        # Return last N records
        return records[-count:]
```

### Integration into `app/runtime/agent_runtime.py`

```python
# app/runtime/agent_runtime.py

from app.audit.audit_logger import AuditLogger

def run_agent(user_message: str) -> dict[str, Any]:
    try:
        plan = create_plan(user_message)
        action = plan.get("action", "answer")
        args = plan.get("args", {})
        
        if action == "answer":
            answer = answer_directly(user_message)
            
            AuditLogger.log_agent_run(
                user_message=user_message,
                plan=plan,
                action=action,
                args=args,
                tool_result=None,
                final_answer=answer,
                status="success",
            )
            
            return {
                "type": "direct_answer",
                "plan": plan,
                "tool_result": None,
                "answer": answer,
            }
        
        tool_result = execute_tool(action, args)
        final_answer = summarize_tool_result(user_message, plan, tool_result)
        
        AuditLogger.log_agent_run(
            user_message=user_message,
            plan=plan,
            action=action,
            args=args,
            tool_result=tool_result,
            final_answer=final_answer,
            status="success",
        )
        
        return {
            "type": "tool_using_agent",
            "plan": plan,
            "tool_result": tool_result,
            "answer": final_answer,
        }
    
    except Exception as e:
        AuditLogger.log_agent_run(
            user_message=user_message,
            plan={},
            action="error",
            args={},
            tool_result=None,
            final_answer="",
            status="error",
            error=str(e),
        )
        raise
```

### New Endpoints

```python
# app/routes/audit_routes.py

from fastapi import APIRouter
from app.audit.audit_logger import AuditLogger

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/recent")
def get_recent_audit_logs(count: int = 20):
    """Get last N audit logs."""
    records = AuditLogger.read_recent(count)
    return {"count": len(records), "records": records}

@router.get("/stats")
def get_audit_stats():
    """Get today's audit stats (actions count, errors, etc.)."""
    records = AuditLogger.read_recent(1000)
    
    action_counts = {}
    error_count = 0
    
    for record in records:
        action = record.get("action", "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1
        if record.get("status") == "error":
            error_count += 1
    
    return {
        "total_runs": len(records),
        "error_count": error_count,
        "action_breakdown": action_counts,
    }
```

## Audit Log Format (JSONL)

One JSON per line, one file per day:

```json
{
  "timestamp": "2026-07-01T11:30:45.123456",
  "user_message": "อ่านไฟล์ project.txt แล้วสรุปให้หน่อย",
  "plan": {
    "action": "read_file",
    "args": {"path": "project.txt"},
    "reason": "User asked to read project.txt"
  },
  "action": "read_file",
  "args": {"path": "project.txt"},
  "tool_result": {
    "tool": "read_file",
    "path": "project.txt",
    "content": "..."
  },
  "final_answer": "ไฟล์ project.txt มีเนื้อหา ...",
  "status": "success",
  "error": null
}
```

## Success Criteria
- ✅ Every agent run logs to `workspace/audit_logs/audit_YYYYMMDD.jsonl`
- ✅ `GET /audit/recent` returns last 20 logs
- ✅ `GET /audit/stats` shows breakdown by action
- ✅ Logs include timestamp, user message, plan, tool result, answer, status
- ✅ Sensitive data is truncated (no huge file contents)

## Sample Queries

```bash
# Get recent logs
curl http://localhost:8000/audit/recent?count=5

# Get today's stats
curl http://localhost:8000/audit/stats

# Manually inspect log file
tail workspace/audit_logs/audit_20260701.jsonl | jq .
```

## Why It Matters
- **Transparency**: Full record of what the agent did and why
- **Debugging**: Can replay agent decisions to understand failures
- **Compliance**: Audit trail for any security/performance reviews
- **Analytics**: See what users ask most, what tools are used most
- **Accountability**: Agent decisions are traceable

## Effort Estimate
- **~3 hours**: Write audit_logger.py, integrate into agent_runtime, add endpoints, test

---

# PHASE 4: Expand Tools (CAPABILITY)

## Objectives
- Add 5 new tools (get_workspace_tree, create_file, append_file, search_files, delete_file-approval)
- Update planner prompt to know about new actions
- Improve tool routing robustness

## What Gets Built

### New Tools in `app/tools/file_tools.py`

```python
def get_workspace_tree(max_depth: int = 3) -> dict[str, Any]:
    """Return folder tree structure."""
    def build_tree(path: Path, depth: int) -> dict:
        if depth >= max_depth:
            return {}
        
        tree = {"type": "dir", "children": {}}
        
        for child in sorted(path.iterdir()):
            if child.name.startswith("."):
                continue
            
            if child.is_dir():
                tree["children"][child.name] = build_tree(child, depth + 1)
            else:
                size = child.stat().st_size
                tree["children"][child.name] = {
                    "type": "file",
                    "size": size
                }
        
        return tree
    
    return {
        "tool": "get_workspace_tree",
        "tree": build_tree(WORKSPACE_DIR, 0),
    }

def create_file(path: str, content: str) -> dict[str, Any]:
    """Create a new file (block if exists)."""
    if not path:
        return {"tool": "create_file", "error": "Missing path"}
    
    target = safe_path(path)
    
    if target.exists():
        return {
            "tool": "create_file",
            "error": f"File already exists: {path}",
        }
    
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    
    return {
        "tool": "create_file",
        "status": "success",
        "created_file": str(target.relative_to(WORKSPACE_DIR)),
        "size": len(content),
    }

def append_file(path: str, content: str) -> dict[str, Any]:
    """Append to existing file."""
    if not path:
        return {"tool": "append_file", "error": "Missing path"}
    
    target = safe_path(path)
    
    if not target.exists():
        return {
            "tool": "append_file",
            "error": f"File not found: {path}",
        }
    
    with open(target, "a", encoding="utf-8") as f:
        f.write(content)
    
    return {
        "tool": "append_file",
        "status": "success",
        "path": path,
        "appended_bytes": len(content),
    }

def search_files(query: str, file_pattern: str = "*.txt") -> dict[str, Any]:
    """Search for keyword in files."""
    if not query:
        return {"tool": "search_files", "error": "Missing search query"}
    
    results = []
    
    for file_path in WORKSPACE_DIR.rglob(file_pattern):
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                if query.lower() in content.lower():
                    # Find line numbers
                    lines_with_match = []
                    for i, line in enumerate(content.split("\n"), 1):
                        if query.lower() in line.lower():
                            lines_with_match.append((i, line.strip()[:100]))
                    
                    results.append({
                        "file": str(file_path.relative_to(WORKSPACE_DIR)),
                        "matches": len(lines_with_match),
                        "lines": lines_with_match[:5],  # First 5 matches
                    })
            except Exception:
                pass
    
    return {
        "tool": "search_files",
        "query": query,
        "pattern": file_pattern,
        "total_matches": len(results),
        "results": results[:10],  # First 10 files
    }
```

### Updated Planner Prompt

```python
# app/runtime/planner.py

def create_plan(user_message: str) -> dict[str, Any]:
    system_prompt = """
You are an AI agent running inside a local AI Environment.

You must choose exactly one action based on what the user asks.

Available actions:

1. answer
Use when no tool is needed. Just answer the user's question.

2. list_files
Use when user asks what files exist in workspace.

3. read_file
Use when user asks to read or inspect a file.
Args: {"path": "filename.txt"}

4. write_note
Use when user asks to save or write a note.
Args: {"content": "markdown note content"}

5. get_workspace_tree
Use when user asks for folder structure or organization.
Args: {} (no args needed)

6. create_file
Use when user asks to create a new file.
Args: {"path": "newfile.md", "content": "file content"}

7. append_file
Use when user asks to add content to existing file.
Args: {"path": "existing.txt", "content": "\\nmore content"}

8. search_files
Use when user asks to search for a keyword in files.
Args: {"query": "keyword", "file_pattern": "*.txt"}

Rules:
- Return ONLY valid JSON
- Do not explain outside JSON
- Choose ONE action
- If multiple actions needed, pick the most relevant

Format:
{
  "action": "answer | list_files | read_file | write_note | get_workspace_tree | create_file | append_file | search_files",
  "args": {},
  "reason": "why you picked this action"
}
"""
    
    content = call_azure_ai(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
    )
    
    return extract_json(content)
```

### Updated Tool Dispatcher

```python
# app/tools/file_tools.py

def execute_tool(action: str, args: dict[str, Any]) -> dict[str, Any]:
    from app.core.policy import check_policy
    
    decision = check_policy(action, args)
    
    if decision.action == PolicyAction.BLOCK:
        return {
            "tool": action,
            "status": "blocked",
            "reason": decision.reason,
        }
    
    if decision.action == PolicyAction.APPROVAL_REQUIRED:
        return {
            "tool": action,
            "status": "approval_required",
            "reason": decision.reason,
        }
    
    # Execute allowed tools
    if action == "list_files":
        return list_files()
    
    if action == "read_file":
        return read_file(args.get("path", ""))
    
    if action == "write_note":
        return write_note(args.get("content", ""))
    
    if action == "get_workspace_tree":
        return get_workspace_tree(args.get("max_depth", 3))
    
    if action == "create_file":
        return create_file(
            args.get("path", ""),
            args.get("content", "")
        )
    
    if action == "append_file":
        return append_file(
            args.get("path", ""),
            args.get("content", "")
        )
    
    if action == "search_files":
        return search_files(
            args.get("query", ""),
            args.get("file_pattern", "*.txt")
        )
    
    return {
        "tool": action,
        "error": f"Unknown action: {action}",
    }
```

## Testing Scenarios

```bash
# User: "สร้างไฟล์ใหม่ชื่อ notes.md ด้วยเนื้อหา hello"
# Agent: create_file with path=notes.md, content=hello

# User: "ค้นหาคำว่า TODO ในไฟล์ทั้งหมด"
# Agent: search_files with query=TODO

# User: "แสดงโครงสร้างของ workspace"
# Agent: get_workspace_tree

# User: "เพิ่มเนื้อหา 'completed' ลงในไฟล์ project.txt"
# Agent: append_file with path=project.txt, content=\ncompleted
```

## Success Criteria
- ✅ All 5 new tools work correctly
- ✅ Planner recognizes all new actions
- ✅ Each tool properly validates input
- ✅ Tools return structured error messages
- ✅ Policy layer applies to all tools
- ✅ Audit logging captures all tool uses

## Effort Estimate
- **~3 hours**: Implement tools, update planner, test scenarios

---

# PHASE 5: Conversation Memory (CONTEXT)

## Objectives
- Maintain conversation history per session
- Pass multi-turn context to Azure AI
- Enable agent to reference previous messages

## What Gets Built

### New Files
- `app/memory/session_store.py` — Session management
- `app/memory/conversation.py` — Conversation history

### Code Example

```python
# app/memory/session_store.py

from uuid import uuid4
from datetime import datetime, timedelta
from typing import Any
from app.memory.conversation import Conversation

class SessionStore:
    """In-memory session store (later: SQLite or Redis)."""
    
    def __init__(self):
        self.sessions: dict[str, Conversation] = {}
    
    def create_session(self, session_id: str | None = None) -> str:
        """Create new session."""
        if not session_id:
            session_id = str(uuid4())
        
        self.sessions[session_id] = Conversation(session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Conversation | None:
        """Get conversation by session ID."""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add message to conversation."""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id].add_message(role, content)
    
    def get_context(self, session_id: str, max_messages: int = 10) -> list[dict]:
        """Get last N messages for context."""
        if session_id not in self.sessions:
            return []
        
        return self.sessions[session_id].get_last_messages(max_messages)

# Global session store
session_store = SessionStore()
```

```python
# app/memory/conversation.py

from datetime import datetime
from typing import Any

class Message:
    def __init__(self, role: str, content: str):
        self.role = role  # "user", "assistant"
        self.content = content
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

class Conversation:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: list[Message] = []
        self.created_at = datetime.utcnow().isoformat()
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation."""
        self.messages.append(Message(role, content))
    
    def get_last_messages(self, count: int = 10) -> list[dict]:
        """Get last N messages."""
        return [m.to_dict() for m in self.messages[-count:]]
    
    def to_openai_format(self, max_messages: int = 10) -> list[dict]:
        """Convert to OpenAI message format."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages[-max_messages:]
        ]
```

### Updated Agent Runtime

```python
# app/routes/chat_routes.py

from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.runtime.agent_runtime import run_agent
from app.memory.session_store import session_store

router = APIRouter()

class AgentRequest(BaseModel):
    message: str
    session_id: str | None = None  # Optional: auto-create if not provided

@router.post("/agent/chat")
def agent_chat(request: AgentRequest):
    # Get or create session
    session_id = request.session_id or session_store.create_session()
    
    # Add user message to conversation
    session_store.add_message(session_id, "user", request.message)
    
    # Get conversation context for AI (last 10 messages)
    context = session_store.get_context(session_id, max_messages=10)
    
    # Run agent with context
    result = run_agent(request.message, context=context)
    
    # Add agent response to conversation
    session_store.add_message(session_id, "assistant", result["answer"])
    
    # Return response with session ID
    return {
        "session_id": session_id,
        "type": result["type"],
        "plan": result["plan"],
        "tool_result": result["tool_result"],
        "answer": result["answer"],
    }

@router.get("/conversation/{session_id}")
def get_conversation(session_id: str):
    """Get full conversation history."""
    conversation = session_store.get_session(session_id)
    
    if not conversation:
        return {"error": "Session not found"}
    
    return {
        "session_id": session_id,
        "created_at": conversation.created_at,
        "message_count": len(conversation.messages),
        "messages": [m.to_dict() for m in conversation.messages],
    }
```

### Updated Planner with Context

```python
# app/runtime/planner.py

def create_plan(user_message: str, context: list[dict] = None) -> dict[str, Any]:
    """Create plan with optional conversation context."""
    
    system_prompt = """
You are an AI agent in a local AI Environment. You have access to conversation history.

Available actions:
1. answer
2. list_files
3. read_file
4. write_note
5. get_workspace_tree
6. create_file
7. append_file
8. search_files

When referencing previous messages, use context. For example:
- User previously asked to read project.txt
- Agent read it and summarized
- Now user says "summarize it again" → use context to understand what file

Return only JSON.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation context
    if context:
        messages.extend(context)
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    content = call_azure_ai(
        messages=messages,
        max_tokens=1024,
    )
    
    return extract_json(content)
```

## Multi-Turn Conversation Example

```
Session: abc123

Turn 1:
User: "อ่านไฟล์ project.txt"
Agent: [reads file] "ไฟล์ project.txt มีเนื้อหา..."
  Context: [{"role": "user", "content": "อ่านไฟล์ project.txt"}, 
            {"role": "assistant", "content": "ไฟล์ project.txt มี..."}]

Turn 2:
User: "สรุปไฟล์นั้นให้หน่อย"
Agent: [remembers project.txt from Turn 1]
       "ไฟล์ project.txt สรุป..."
  Context: [prev message + new turn]

Turn 3:
User: "เขียน note ว่าสรุป content"
Agent: [remembers project.txt content + summary]
       [creates note with summary]
  Context: [all previous + new turn]
```

## Success Criteria
- ✅ Each client gets unique session_id
- ✅ Conversation history persists in memory (server uptime)
- ✅ Agent references previous context naturally
- ✅ `GET /conversation/{session_id}` returns full history
- ✅ POST `/agent/chat` accepts optional session_id parameter

## Future Enhancement
- Persist sessions to SQLite for survival across restarts
- TTL for old sessions (auto-cleanup after 7 days)
- Export conversation as markdown

## Effort Estimate
- **~4 hours**: Write session store, update routes, integrate with planner

---

# PHASE 6: API Surface (ENDPOINTS)

## Objectives
- Add endpoints for audit, workspace, conversation management
- Enable frontend to query all agent state
- RESTful, well-documented API

## New Endpoints

### Workspace Endpoints

```python
# app/routes/workspace_routes.py

from fastapi import APIRouter
from app.tools.file_tools import (
    list_files, read_file, get_workspace_tree
)

router = APIRouter(prefix="/workspace", tags=["workspace"])

@router.get("/files")
def get_workspace_files():
    """List all files in workspace."""
    return list_files()

@router.get("/tree")
def get_workspace_structure(max_depth: int = 3):
    """Get folder tree structure."""
    return get_workspace_tree(max_depth)

@router.get("/read")
def read_workspace_file(path: str):
    """Read a specific file."""
    return read_file(path)

@router.get("/size")
def get_workspace_size():
    """Get total workspace size in bytes."""
    from pathlib import Path
    
    total_size = 0
    file_count = 0
    
    for path in WORKSPACE_DIR.rglob("*"):
        if path.is_file():
            total_size += path.stat().st_size
            file_count += 1
    
    return {
        "total_files": file_count,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }
```

### Audit Endpoints (expanded)

```python
# app/routes/audit_routes.py

from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/recent")
def get_recent_logs(count: int = 20):
    """Get last N audit logs."""
    return AuditLogger.read_recent(count)

@router.get("/stats")
def get_audit_stats(days: int = 1):
    """Get stats for last N days."""
    # Implementation: read all log files for date range
    pass

@router.get("/by-action/{action}")
def get_logs_by_action(action: str, count: int = 10):
    """Get logs for specific action (read_file, write_note, etc)."""
    all_logs = AuditLogger.read_recent(1000)
    return [log for log in all_logs if log.get("action") == action][:count]

@router.get("/errors")
def get_error_logs(count: int = 50):
    """Get all error logs."""
    all_logs = AuditLogger.read_recent(1000)
    return [log for log in all_logs if log.get("status") == "error"][:count]
```

### Session Endpoints

```python
# app/routes/session_routes.py

from fastapi import APIRouter
from app.memory.session_store import session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/new")
def create_new_session():
    """Create new conversation session."""
    session_id = session_store.create_session()
    return {"session_id": session_id}

@router.get("/{session_id}")
def get_session_info(session_id: str):
    """Get session metadata and message count."""
    conv = session_store.get_session(session_id)
    
    if not conv:
        return {"error": "Session not found"}
    
    return {
        "session_id": session_id,
        "created_at": conv.created_at,
        "message_count": len(conv.messages),
        "last_message": conv.messages[-1].to_dict() if conv.messages else None,
    }

@router.get("/{session_id}/messages")
def get_session_messages(session_id: str, limit: int = 50):
    """Get all messages in session."""
    conv = session_store.get_session(session_id)
    
    if not conv:
        return {"error": "Session not found"}
    
    return {
        "session_id": session_id,
        "messages": [m.to_dict() for m in conv.messages[-limit:]],
    }
```

### System Endpoints

```python
# app/routes/system_routes.py

from fastapi import APIRouter
from app.core.config import AZURE_OPENAI_MODEL
from app.tools.file_tools import execute_tool

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/info")
def get_system_info():
    """Get system info."""
    return {
        "service": "tcc-ai-environment-agent",
        "model": AZURE_OPENAI_MODEL,
        "version": "0.2.0",  # Post-refactor
    }

@router.get("/health")
def health_check():
    """Health check."""
    return {"status": "ok"}

@router.get("/config")
def get_config():
    """Get safe config (no secrets)."""
    from app.core.config import WORKSPACE_DIR, FRONTEND_DIR, AUDIT_LOG_DIR
    
    return {
        "workspace_dir": str(WORKSPACE_DIR),
        "frontend_dir": str(FRONTEND_DIR),
        "audit_log_dir": str(AUDIT_LOG_DIR),
        "model": AZURE_OPENAI_MODEL,
    }
```

## Updated app/main.py

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import FRONTEND_DIR
from app.routes.frontend_routes import router as frontend_router
from app.routes.chat_routes import router as chat_router
from app.routes.workspace_routes import router as workspace_router
from app.routes.audit_routes import router as audit_router
from app.routes.session_routes import router as session_router
from app.routes.system_routes import router as system_router

app = FastAPI(
    title="TCC AI Environment Agent",
    version="0.2.0",
    description="Local AI Agent Runtime with secure workspace & audit logging",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Routers
app.include_router(frontend_router)
app.include_router(chat_router)
app.include_router(workspace_router)
app.include_router(audit_router)
app.include_router(session_router)
app.include_router(system_router)
```

## API Summary

```
Frontend:
  GET  /
  GET  /chat
  GET  /health
  GET  /debug/env
  GET  /debug/frontend

Chat:
  POST /agent/chat

Workspace:
  GET  /workspace/files
  GET  /workspace/tree
  GET  /workspace/read?path=...
  GET  /workspace/size

Audit:
  GET  /audit/recent
  GET  /audit/stats
  GET  /audit/by-action/{action}
  GET  /audit/errors

Sessions:
  POST /sessions/new
  GET  /sessions/{session_id}
  GET  /sessions/{session_id}/messages

System:
  GET  /system/info
  GET  /system/health
  GET  /system/config
```

## Success Criteria
- ✅ All endpoints documented in `/docs` (Swagger)
- ✅ All endpoints return structured JSON
- ✅ No sensitive data exposed in responses
- ✅ All endpoints logged to audit trail

## Effort Estimate
- **~3 hours**: Write all route files, integrate, test endpoints

---

# PHASE 7: UI Upgrade (USER EXPERIENCE)

## Objectives
- Migrate from simple chat to Cursor/OpenClaw-style 3-pane layout
- Real-time plan/tool result visibility
- Status log & session management

## New UI Structure

```
┌─────────────────────────────────────────────────────────┐
│               TCC AI Environment Agent                   │
└─────────────────────────────────────────────────────────┘

┌────────────┬─────────────────────────┬──────────────────┐
│  SIDEBAR   │      CENTER CHAT        │   RIGHT PANEL    │
│            │                         │                  │
│  📁 Workspace                        │  Agent Plan      │
│  ├─ project.txt                      │  ┌─────────────┐ │
│  ├─ notes/                           │  │ Action:     │ │
│  │  ├─ note_1.md                     │  │ read_file   │ │
│  │  └─ note_2.md                     │  │             │ │
│  └─ ...                              │  │ Args:       │ │
│                                      │  │ {path: ...} │ │
│  🔧 Tools                            │  └─────────────┘ │
│  ├─ list_files                       │                  │
│  ├─ read_file                        │  Tool Result     │
│  ├─ write_note                       │  ┌─────────────┐ │
│  ├─ create_file                      │  │ tool: ...   │ │
│  └─ ...                              │  │ status: ok  │ │
│                                      │  │ content: ..│ │
│  📊 Audit                            │  └─────────────┘ │
│  ├─ Recent logs                      │                  │
│  ├─ Stats                            │  Raw JSON        │
│  └─ Export                           │  ┌─────────────┐ │
│                                      │  │ {           │ │
│  ⚙️ Settings                         │  │  "type": .. │ │
│  ├─ Session ID                       │  │  "plan": .. │ │
│  ├─ Theme (dark/light)               │  │ }           │ │
│  └─ Clear history                    │  └─────────────┘ │
│                                      │                  │
└────────────┴─────────────────────────┴──────────────────┘

┌─────────────────────────────────────────────────────────┐
│ BOTTOM STATUS BAR                                       │
│ Session: abc123 | Model: gpt-5.1 | Status: Ready       │
│ Last action: read_file | Error count: 0                │
└─────────────────────────────────────────────────────────┘
```

### New Frontend Files

```python
# frontend/index.html (replaces chat.html)
# Builds the 3-pane layout

# frontend/js/ui.js
# Handles pane rendering, real-time updates

# frontend/js/api.js
# Abstracts HTTP calls to /agent/chat, /audit/*, /workspace/*

# frontend/js/session.js
# Session management (create, load, persist)

# frontend/css/layout.css
# 3-pane layout with flexbox

# frontend/css/components.css
# Component styles (sidebar, cards, logs)
```

### Key Features

```javascript
// frontend/js/app.js

class AgentUI {
    constructor() {
        this.sessionId = this.loadSessionId();
        this.messages = [];
    }
    
    async sendMessage(text) {
        // 1. Show user message
        this.addMessageToChat("user", text);
        
        // 2. Show "Thinking..." in center
        this.showThinking();
        
        // 3. Call API
        const response = await fetch("/agent/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: text,
                session_id: this.sessionId
            })
        });
        
        const data = await response.json();
        
        // 4. Show agent plan in right panel (real-time)
        this.showPlan(data.plan);
        
        // 5. Show tool result if applicable
        if (data.tool_result) {
            this.showToolResult(data.tool_result);
        }
        
        // 6. Show final answer in chat
        this.addMessageToChat("assistant", data.answer);
        
        // 7. Update status bar
        this.updateStatus(data);
    }
    
    showPlan(plan) {
        document.getElementById("plan-panel").innerHTML = `
            <div class="plan">
                <div class="plan-action">Action: ${plan.action}</div>
                <div class="plan-reason">${plan.reason}</div>
                <div class="plan-args"><pre>${JSON.stringify(plan.args, null, 2)}</pre></div>
            </div>
        `;
    }
    
    // ... more methods
}
```

## Success Criteria
- ✅ 3-pane layout renders correctly on desktop (1200px+)
- ✅ Agent plan shows in real-time as it plans
- ✅ Tool results visible before final answer
- ✅ Raw JSON expandable in right panel
- ✅ Sidebar shows workspace tree, recent audit logs
- ✅ Session ID visible, can create new session
- ✅ Responsive on tablet (stacks panes)

## Responsive Breakpoints

```css
/* Desktop (1200px+): 3-pane layout */
@media (min-width: 1200px) {
    .container {
        display: grid;
        grid-template-columns: 250px 1fr 350px;
    }
}

/* Tablet (768px-1199px): Stack vertically */
@media (max-width: 1199px) {
    .container {
        display: flex;
        flex-direction: column;
    }
}

/* Mobile (< 768px): Single column, hide sidebar */
@media (max-width: 767px) {
    .sidebar { display: none; }
}
```

## Effort Estimate
- **~6-8 hours**: Design layout, build components, integrate API calls, test responsiveness

---

# PHASE 8: Testing (RELIABILITY)

## Objectives
- Add unit tests for all core modules
- Add integration tests for API endpoints
- Add end-to-end tests for agent flows

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── test_parser.py            # JSON parsing tests
│   ├── test_policy.py            # Policy layer tests
│   ├── test_file_tools.py        # Workspace tool tests
│   └── test_audit_logger.py      # Audit logging tests
├── integration/
│   ├── test_agent_runtime.py     # Full agent flow tests
│   └── test_azure_client.py      # Azure API mock tests
└── e2e/
    ├── test_chat_endpoint.py     # /agent/chat endpoint tests
    └── test_conversation_flow.py # Multi-turn conversation tests
```

### Example Tests

```python
# tests/unit/test_parser.py

import pytest
from app.runtime.parser import extract_json

def test_extract_json_valid():
    """Test extraction of valid JSON."""
    text = '{"action": "answer", "args": {}}'
    result = extract_json(text)
    assert result["action"] == "answer"

def test_extract_json_with_markdown():
    """Test extraction of JSON wrapped in markdown."""
    text = '```json\n{"action": "list_files"}\n```'
    result = extract_json(text)
    assert result["action"] == "list_files"

def test_extract_json_fallback():
    """Test fallback when JSON invalid."""
    text = "This is not JSON, just answer"
    result = extract_json(text)
    assert result["action"] == "answer"

# tests/unit/test_policy.py

from app.core.policy import check_policy, PolicyAction

def test_policy_block_env():
    """Test that .env reads are blocked."""
    decision = check_policy("read_file", {"path": ".env"})
    assert decision.action == PolicyAction.BLOCK

def test_policy_allow_read_project():
    """Test that safe file reads are allowed."""
    decision = check_policy("read_file", {"path": "project.txt"})
    assert decision.action == PolicyAction.ALLOW

def test_policy_approval_delete():
    """Test that delete requires approval."""
    decision = check_policy("delete_file", {"path": "file.txt"})
    assert decision.action == PolicyAction.APPROVAL_REQUIRED

# tests/integration/test_agent_runtime.py

import pytest
from unittest.mock import patch, MagicMock
from app.runtime.agent_runtime import run_agent

@patch('app.core.azure_client.call_azure_ai')
def test_agent_answer_directly(mock_azure):
    """Test agent answering directly (no tool)."""
    mock_azure.return_value = '{"action": "answer", "args": {}}'
    
    result = run_agent("Hello, how are you?")
    
    assert result["type"] == "direct_answer"
    assert result["answer"] is not None
    assert result["tool_result"] is None

@patch('app.core.azure_client.call_azure_ai')
def test_agent_uses_tool(mock_azure, tmp_path):
    """Test agent using a tool."""
    # Mock planner response
    mock_azure.side_effect = [
        '{"action": "list_files", "args": {}}',  # Planner
        'Files in workspace...'  # Summarizer
    ]
    
    result = run_agent("What files are in workspace?")
    
    assert result["type"] == "tool_using_agent"
    assert result["tool_result"] is not None
    assert result["tool_result"]["tool"] == "list_files"

# tests/e2e/test_chat_endpoint.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_endpoint_returns_answer():
    """Test /agent/chat endpoint."""
    response = client.post(
        "/agent/chat",
        json={"message": "Hello"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "plan" in data

def test_chat_endpoint_with_session():
    """Test /agent/chat with session tracking."""
    # Message 1
    response1 = client.post(
        "/agent/chat",
        json={"message": "Read project.txt"}
    )
    session_id = response1.json()["session_id"]
    
    # Message 2 (same session)
    response2 = client.post(
        "/agent/chat",
        json={
            "message": "Summarize what you just read",
            "session_id": session_id
        }
    )
    
    assert response2.status_code == 200
    assert response2.json()["session_id"] == session_id
```

## Test Coverage Goals

```
app/core/config.py        → 80% (env loading, paths)
app/core/azure_client.py  → 90% (mock Azure API)
app/runtime/parser.py     → 95% (JSON parsing edge cases)
app/runtime/planner.py    → 70% (mock Azure planner)
app/core/policy.py        → 95% (all policy rules)
app/tools/file_tools.py   → 85% (safe_path, tool funcs)
app/audit/audit_logger.py → 90% (logging, reading)
app/memory/session_store  → 85% (sessions, messages)
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run specific test
pytest tests/unit/test_parser.py::test_extract_json_valid

# Run with verbose output
pytest -v
```

## CI/CD Integration (future)

```yaml
# .github/workflows/test.yml

name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt pytest
      - run: pytest --cov=app
```

## Success Criteria
- ✅ 80%+ code coverage
- ✅ All critical paths tested (policy, parser, tools)
- ✅ CI passes on every commit
- ✅ Test suite runs in < 5 seconds

## Effort Estimate
- **~6 hours**: Write unit + integration tests, set up CI

---

# PHASE 9: Containerization (PORTABILITY)

## Objectives
- Package app as Docker image
- Enable easy deployment on any server
- docker-compose for local dev environment

## Docker Setup

### Dockerfile

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create workspace directory
RUN mkdir -p workspace/audit_logs workspace/notes

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      AZURE_OPENAI_BASE_URL: ${AZURE_OPENAI_BASE_URL}
      AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY}
      AZURE_OPENAI_MODEL: ${AZURE_OPENAI_MODEL}
    volumes:
      - ./workspace:/app/workspace
      - ./frontend:/app/frontend
    restart: unless-stopped
```

### .dockerignore

```
.git
.gitignore
.venv
venv
__pycache__
*.pyc
.pytest_cache
.coverage
htmlcov
.idea
.vscode
*.log
.env
```

### Environment File

```bash
# .env.example (commit this, not .env)

AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_MODEL=gpt-5.1-codex-mini
```

## Running with Docker

```bash
# Build image
docker build -t tcc-agent .

# Run locally
docker run -p 8000:8000 \
  -e AZURE_OPENAI_BASE_URL=$AZURE_OPENAI_BASE_URL \
  -e AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY \
  -v $(pwd)/workspace:/app/workspace \
  tcc-agent

# Or with docker-compose
cp .env.example .env
# (edit .env with your credentials)
docker-compose up

# Access on http://localhost:8000/chat
```

## Kubernetes Deployment (optional)

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: tcc-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tcc-agent
  template:
    metadata:
      labels:
        app: tcc-agent
    spec:
      containers:
      - name: agent
        image: your-registry/tcc-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_OPENAI_BASE_URL
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: base-url
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        volumeMounts:
        - name: workspace
          mountPath: /app/workspace
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: agent-workspace-pvc
```

## Success Criteria
- ✅ Docker image builds successfully
- ✅ Container runs and serves /chat
- ✅ `docker-compose up` works end-to-end
- ✅ Workspace persists across container restarts
- ✅ Health check passes

## Effort Estimate
- **~2 hours**: Write Dockerfile, docker-compose, test locally

---

# STRETCH GOALS (Beyond Phase 9)

## Stretch 1: 24/7 Scheduled Tasks

**Goal**: Agent periodically runs tasks without user prompts.

**Example**:
```python
# app/scheduler/tasks.py

from apscheduler.schedulers.background import BackgroundScheduler
from app.runtime.agent_runtime import run_agent

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=0)
def daily_morning_briefing():
    """Every day at 9 AM, agent summarizes workspace changes."""
    result = run_agent("Summarize any new files in workspace since yesterday")
    print(f"Morning briefing: {result['answer']}")

@scheduler.scheduled_job('interval', minutes=60)
def hourly_cleanup():
    """Every hour, clean up old temporary files."""
    result = run_agent("Delete any files in workspace/temp/ older than 1 day")
    print(f"Cleanup result: {result}")

scheduler.start()
```

## Stretch 2: Multi-User Support

**Goal**: Support multiple users with separate workspaces.

**Schema**:
```python
# app/memory/user_store.py

class User:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.workspace_dir = WORKSPACE_DIR / user_id
        self.sessions = {}
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

# Routes require user_id
@router.post("/users/{user_id}/agent/chat")
def agent_chat_for_user(user_id: str, request: AgentRequest):
    user = user_store.get_or_create_user(user_id)
    # Run agent in user's workspace
    ...
```

## Stretch 3: Integrations

**Goal**: Connect to external services (Slack, GitHub, Email).

**Examples**:
```python
# app/integrations/slack_bot.py

from slack_bolt import App
from app.runtime.agent_runtime import run_agent

slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@slack_app.message(".*")
def handle_message(message, say):
    """Respond to Slack messages."""
    result = run_agent(message["text"])
    say(result["answer"])

# app/integrations/github_handler.py

# Listen for GitHub webhooks
@router.post("/webhooks/github")
def github_webhook(payload: dict):
    """React to GitHub events."""
    result = run_agent(f"New GitHub event: {payload['action']} on {payload['repository']}")
    # Could auto-create issues, comments, PRs, etc.
    ...
```

## Stretch 4: Web-Based Administration Panel

**Goal**: Dashboard for managing agent, viewing logs, settings.

**Features**:
- Real-time audit log viewer with search
- Session history browser
- Tool execution history
- Performance metrics
- Policy management UI
- Backup/export controls

## Stretch 5: Advanced Memory (RAG)

**Goal**: Agent can remember and search across all past conversations.

**Implementation**:
- Embed conversation summaries using local model or Azure embeddings
- Store in vector DB (Chroma, Pinecone)
- On new question: "Find similar past conversations"
- Use similar past context in prompt

---

# Summary Table

| Phase | Goal | Key Files | Effort | Dependencies |
|-------|------|-----------|--------|--------------|
| 0 ✅ | Git & Deps | `.gitignore`, `requirements.txt` | 30 min | None |
| 1 ✅ | Refactor | 11 app modules | 2-3 hrs | Phase 0 |
| 2 | Policy | `app/core/policy.py` | 2 hrs | Phase 1 |
| 3 | Audit | `app/audit/audit_logger.py` | 3 hrs | Phase 2 |
| 4 | Tools | `app/tools/file_tools.py` (expand) | 3 hrs | Phase 3 |
| 5 | Memory | `app/memory/` modules | 4 hrs | Phase 1 |
| 6 | API | New route modules | 3 hrs | Phase 5 |
| 7 | UI | `frontend/` rebuild | 6-8 hrs | Phase 6 |
| 8 | Testing | `tests/` suite | 6 hrs | All above |
| 9 | Docker | `Dockerfile`, `docker-compose.yml` | 2 hrs | All above |
| S1 | 24/7 Tasks | `app/scheduler/` | 3 hrs | Phase 9 |
| S2 | Multi-user | `app/memory/user_store.py` | 4 hrs | Phase 9 |
| S3 | Integrations | `app/integrations/` | 5+ hrs | Phase 9 |
| S4 | Admin Panel | New frontend app | 8+ hrs | Phase 9 |
| S5 | RAG Memory | Vector DB + embeddings | 6+ hrs | Phase 9 |

---

# Recommended Implementation Order

1. **Phase 1-3** (1-2 weeks)
   - Refactor ✅
   - Policy layer
   - Audit logs
   - *Result: Secure, transparent agent with basic tools*

2. **Phase 4-5** (1 week)
   - More tools
   - Conversation memory
   - *Result: Multi-turn agent with file operations*

3. **Phase 6-7** (1-2 weeks)
   - API surface
   - UI upgrade
   - *Result: Production-ready frontend + API*

4. **Phase 8-9** (1 week)
   - Testing
   - Containerization
   - *Result: Tested, deployed app*

5. **Stretch Goals** (as needed)
   - 24/7 tasks
   - Multi-user
   - Integrations
   - Advanced features

---

**Total Effort**: ~40-50 hours for core phases → production-ready local AI agent runtime.

Generated: 2026-07-01

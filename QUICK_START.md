# Quick Start After Refactor

## 1. Verify the Refactor

```bash
# Validate all imports work
python validate_refactor.py
```

Expected: Shows all modules import successfully, lists project structure.

---

## 2. Run the Server

Choose one:

```bash
# Option A: Direct Python (recommended for development)
python main.py

# Option B: Uvicorn CLI
python -m uvicorn main:app --reload --port 8000

# Option C: Uvicorn on app module
python -m uvicorn app.main:app --reload --port 8000
```

Expected: Server starts on `http://localhost:8000` with auto-reload enabled.

---

## 3. Test the App

### In Browser
- Chat UI: `http://localhost:8000/chat`
- API docs: `http://localhost:8000/docs`

### Via PowerShell

**Health check:**
```powershell
irm "http://localhost:8000/health"
```

**Test agent:**
```powershell
$body = '{"message":"Hello, what can you do?"}'
Invoke-RestMethod -Uri "http://localhost:8000/agent/chat" -Method POST `
  -ContentType "application/json" -Body $body
```

**Debug env:**
```powershell
irm "http://localhost:8000/debug/env"
```

---

## 4. Project Structure

```
TCC Project/
├── main.py                      ← Entry point
├── requirements.txt             ← Pinned dependencies
├── .gitignore                   ← Git ignore patterns
├── validate_refactor.py         ← Validation script
├── PHASE_0_1_SUMMARY.md         ← This refactor overview
├── app/
│   ├── main.py                  ← FastAPI app factory
│   ├── core/
│   │   ├── config.py            ← Paths & env
│   │   └── azure_client.py      ← Azure API calls
│   ├── runtime/
│   │   ├── agent_runtime.py     ← Agent orchestration
│   │   ├── planner.py           ← Planning & answering
│   │   └── parser.py            ← JSON parsing
│   ├── tools/
│   │   └── file_tools.py        ← Workspace tools
│   └── routes/
│       ├── utils.py             ← Route helpers
│       ├── frontend_routes.py   ← Frontend endpoints
│       └── chat_routes.py       ← Agent endpoint
├── frontend/
│   ├── chat.html
│   ├── style.css
│   └── app.js
└── workspace/
    ├── audit_logs/              ← For Phase 3
    └── notes/
```

---

## 5. Key Changes from Original

| Aspect | Before | After |
|--------|--------|-------|
| **File count** | 1 file (450 lines) | 11 modules (70–80 lines each) |
| **Config** | Top of main.py | `app/core/config.py` |
| **Azure calls** | Inline in routes | `app/core/azure_client.py` |
| **Tools** | Inline functions | `app/tools/file_tools.py` |
| **Routes** | All in main.py | Split into `frontend_routes.py`, `chat_routes.py` |
| **Entry point** | `python main.py` (old) → Error | `python main.py` (new) → Works ✓ |
| **Testing** | Hard | Easy (test modules independently) |

---

## 6. Next Steps

After verification, start **Phase 2: Policy Layer**
- Add `app/core/policy.py`
- Insert `check_policy()` before tool execution
- Block unsafe operations

See `REFACTOR_PROGRESS.md` for full roadmap.

---

## Troubleshooting

### "Module not found" errors
```bash
python validate_refactor.py
```
This will pinpoint the issue.

### "Can't find chat.html"
Verify `frontend/` directory exists:
```bash
ls -l frontend/
```

### ".env not loading"
Check that `.env` is in the project root and readable:
```bash
cat .env | head
```

### Port 8000 already in use
Use a different port:
```bash
python -m uvicorn main:app --port 8001
```

---

## Environment Variables

Ensure `.env` has:
```
AZURE_OPENAI_BASE_URL=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_MODEL=gpt-5.1-codex-mini
```

**Never commit `.env` to git** — already in `.gitignore`.

---

## Initial Git Commit

Once tested:
```bash
git add .
git commit -m "Phase 0 & 1: Init git, pin deps, refactor main.py into modules"
```

---

Last updated: 2026-07-01 11:28 UTC+7

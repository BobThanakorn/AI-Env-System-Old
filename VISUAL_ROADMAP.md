# Visual Roadmap: TCC AI Environment Agent

## Timeline View

```
CURRENT (Phase 1 ✅)
│
├─ Phase 1: Refactor ✅
│  └─ 11 modules, clean structure
│
├─ Phase 2: Policy (guardrails)
│  └─ Block unsafe ops, approval workflow
│
├─ Phase 3: Audit (transparency)
│  └─ Persistent logs, query endpoints
│
├─ Phase 4: Tools (capability)
│  └─ 5 new tools, expanded planner
│
├─ Phase 5: Memory (context)
│  └─ Session store, multi-turn conversations
│
├─ Phase 6: API (integration)
│  └─ Workspace, audit, session endpoints
│
├─ Phase 7: UI (UX)
│  └─ 3-pane layout, real-time updates
│
├─ Phase 8: Testing (reliability)
│  └─ 80%+ coverage, CI pipeline
│
└─ Phase 9: Docker (portability)
   └─ Containerization, deployment ready
   
   Stretch Goals:
   ├─ 24/7 Tasks (scheduling)
   ├─ Multi-user (users/workspaces)
   ├─ Integrations (Slack, GitHub)
   ├─ Admin Panel (web dashboard)
   └─ RAG Memory (semantic search)
```

---

## Feature Matrix

```
┌──────────────────┬──────┬────┬────┬────┬────┬────┬────┬────┬────┐
│                  │ P0  │ P1 │ P2 │ P3 │ P4 │ P5 │ P6 │ P7 │ P8 │
├──────────────────┼──────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ Chat             │ ✅   │ ✅ │ ✅ │ ✅ │ ✅ │ ✅*│ ✅ │ ✅*│ ✅ │
│ File Tools       │ ✅   │ ✅ │ ✅ │ ✅ │ ✅*│ ✅ │ ✅ │ ✅ │ ✅ │
│ Policy/Safety    │      │    │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │
│ Audit Logs       │      │    │    │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │
│ Tool Coverage    │      │    │    │    │ ✅*│ ✅ │ ✅ │ ✅ │ ✅ │
│ Conversation     │      │    │    │    │    │ ✅*│ ✅ │ ✅ │ ✅ │
│ API Endpoints    │      │    │    │    │    │    │ ✅ │ ✅ │ ✅ │
│ Modern UI        │      │    │    │    │    │    │    │ ✅*│ ✅ │
│ Test Coverage    │      │    │    │    │    │    │    │    │ ✅*│
│ Docker/Deploy    │      │    │    │    │    │    │    │    │    │
└──────────────────┴──────┴────┴────┴────┴────┴────┴────┴────┴────┘

✅  = Fully implemented
✅* = Enhanced/upgraded
    = Not applicable yet
```

---

## Architecture Evolution

### Phase 1: Clean Code
```
User
 ↓
API (/agent/chat)
 ↓
Agent Runtime
 ├─ Planner
 ├─ Tool Router
 └─ Tools (basic 3)
```

### Phase 2-3: Secure & Transparent
```
User
 ↓
API (/agent/chat)
 ↓
Agent Runtime
 ├─ Planner
 ├─ Policy Check ← NEW
 ├─ Tool Router
 ├─ Tools
 └─ Audit Log ← NEW
```

### Phase 4-5: Capable & Context-Aware
```
User
 ↓
API (/agent/chat, /sessions/*, /workspace/*)
 ↓
Session Manager ← NEW
 ↓
Agent Runtime
 ├─ Planner (with context)
 ├─ Policy Check
 ├─ Tool Router
 ├─ Tools (5+ expanded) ← NEW
 └─ Audit Log
```

### Phase 6-7: Full API + Modern UI
```
┌─ Web UI (3-pane) ← NEW
├─ Mobile UI (responsive)
└─ Programmatic API ← NEW

All connecting to:
Agent Runtime with all P1-5 features
```

### Phase 8-9: Production
```
Docker Container
├─ Full test suite
├─ CI/CD pipelines
└─ Multi-env deployment (dev/staging/prod)
```

---

## Capability Growth

```
Phase 1: MVP
┌─────────────────────────────────┐
│ Ask AI, list/read/write files   │
└─────────────────────────────────┘
        ↓ (Phase 2-3)
Phase 2-3: Secure & Observable
┌─────────────────────────────────┐
│ + Policy layer                  │
│ + Full audit trail              │
│ + Query audit logs              │
└─────────────────────────────────┘
        ↓ (Phase 4-5)
Phase 4-5: Extensible & Aware
┌─────────────────────────────────┐
│ + More tools (create, append)   │
│ + Multi-turn context            │
│ + Session management            │
└─────────────────────────────────┘
        ↓ (Phase 6-7)
Phase 6-7: Integrated & Accessible
┌─────────────────────────────────┐
│ + REST API for all features     │
│ + Modern 3-pane UI              │
│ + Real-time plan/result display │
└─────────────────────────────────┘
        ↓ (Phase 8-9)
Phase 8-9: Production-Ready
┌─────────────────────────────────┐
│ + 80%+ test coverage            │
│ + Docker containerization       │
│ + Deployment pipelines          │
└─────────────────────────────────┘
        ↓ (Stretch)
Production + Advanced
┌─────────────────────────────────┐
│ + 24/7 scheduled tasks          │
│ + Multi-user support            │
│ + External integrations         │
│ + Admin dashboard               │
│ + Semantic memory (RAG)         │
└─────────────────────────────────┘
```

---

## Effort Estimate by Phase

```
Phase 0: 30 min    ████░░░░░░░░░░░░░░░░░░░░ Git & deps
Phase 1: 3 hrs     ██████████████████░░░░░░░ Refactor
Phase 2: 2 hrs     ████████░░░░░░░░░░░░░░░░░ Policy
Phase 3: 3 hrs     ████████████░░░░░░░░░░░░░ Audit
Phase 4: 3 hrs     ████████████░░░░░░░░░░░░░ Tools
Phase 5: 4 hrs     ██████████████░░░░░░░░░░░ Memory
Phase 6: 3 hrs     ████████████░░░░░░░░░░░░░ API
Phase 7: 7 hrs     ████████████████████░░░░░ UI
Phase 8: 6 hrs     ██████████████████░░░░░░░ Testing
Phase 9: 2 hrs     ████████░░░░░░░░░░░░░░░░░ Docker

Core (0-9): ~33 hours ← Production ready
Stretch:    15+ hours  ← Advanced features
```

---

## Success Metrics by Phase

### Phase 1 ✅
- [x] All modules import successfully
- [x] All endpoints work identically
- [x] Can run `validate_refactor.py`
- [x] Server starts on port 8000

### Phase 2
- [ ] `check_policy()` blocks .env reads
- [ ] Delete operations require approval
- [ ] All tools respect policy decisions

### Phase 3
- [ ] Each run logs to JSONL
- [ ] `GET /audit/recent` returns 20 records
- [ ] Logs persist across restarts

### Phase 4
- [ ] Planner recognizes 8 actions
- [ ] All 8 tools execute correctly
- [ ] Search finds keywords in files
- [ ] Tree structure displays folders

### Phase 5
- [ ] Session IDs persist conversations
- [ ] Agent references previous context
- [ ] Multi-turn Q&A works naturally

### Phase 6
- [ ] `/workspace/*` endpoints work
- [ ] `/audit/*` endpoints work
- [ ] `/sessions/*` endpoints work
- [ ] All responses are JSON

### Phase 7
- [ ] 3-pane layout renders
- [ ] Plan shows real-time
- [ ] Tool results visible
- [ ] Responsive on mobile

### Phase 8
- [ ] 80%+ code coverage
- [ ] All critical tests pass
- [ ] CI pipeline passes
- [ ] Test suite < 5s

### Phase 9
- [ ] Docker image builds
- [ ] Container runs end-to-end
- [ ] Workspace persists
- [ ] Health check passes

---

## Dependencies & Blockers

```
Phase 1 ✅
  └─ Phase 2 (needs Phase 1 structure)
      └─ Phase 3 (needs Phase 2 checks)
          └─ Phase 4 (needs Phase 3 logging)
              └─ Phase 5 (independent, but builds on 1)
                  ├─ Phase 6 (needs 5 for endpoints)
                  └─ Phase 7 (needs 6 for API)
                      └─ Phase 8 (tests all above)
                          └─ Phase 9 (packages all above)
```

**Note**: Phase 5 (Memory) doesn't strictly depend on Phase 2-4, but Phase 6+ do.

**Optimal path**: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

---

## Quick Reference: What to Implement Next

If you want to continue from Phase 1:

### Start Phase 2 (Policy Layer)
```bash
1. Create app/core/policy.py
2. Import in app/tools/file_tools.py before execute_tool()
3. Test: curl /agent/chat with read_file, path=.env (should block)
```

**Files to touch**:
- ✨ Create: `app/core/policy.py`
- 🔧 Modify: `app/tools/file_tools.py`
- ✅ Test: `tests/unit/test_policy.py` (Phase 8)

### Or Start Phase 5 (Memory) in Parallel
```bash
1. Create app/memory/session_store.py
2. Create app/memory/conversation.py
3. Modify app/routes/chat_routes.py to use sessions
4. Modify app/runtime/planner.py to use context
```

**Files to touch**:
- ✨ Create: `app/memory/session_store.py`
- ✨ Create: `app/memory/conversation.py`
- 🔧 Modify: `app/routes/chat_routes.py`
- 🔧 Modify: `app/runtime/planner.py`
- ✅ Test: `tests/integration/test_conversation.py` (Phase 8)

---

## Key Decisions Made

✅ **Python + FastAPI**: Type-safe, fast, well-documented
✅ **Local-first**: All data stays on device (secrets safe)
✅ **Azure AI**: Powerful, flexible, cost-effective
✅ **Modular structure**: Easy to test, extend, maintain
✅ **JSONL audit**: Simple, readable, searchable
✅ **In-memory sessions**: Fast, no DB needed yet
✅ **Docker-ready**: No hardcoded paths, env-driven
✅ **REST API**: Standard, well-understood, scalable

---

Generated: 2026-07-01 13:39 UTC+7

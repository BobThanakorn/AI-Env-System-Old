print("step1")
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
print("step2")
from app.core.config import FRONTEND_DIR
print("step3 FRONTEND_DIR", FRONTEND_DIR)
from app.routes.frontend_routes import router as frontend_router
print("step4 frontend routes", [r.path for r in frontend_router.routes])
from app.routes.chat_routes import router as chat_router
print("step5 chat routes", [r.path for r in chat_router.routes])
from app.routes.file_routes import router as file_router
print("step6 file routes", [r.path for r in file_router.routes])

app = FastAPI(title="TCC AI Environment Agent")
print("step7 app created")

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)
print("step8 mounted static")

app.include_router(frontend_router)
print("step9 included frontend", len(app.routes))
app.include_router(chat_router)
print("step10 included chat", len(app.routes))
app.include_router(file_router)
print("step11 included file", len(app.routes))
print("final routes", sorted({getattr(r, "path", None) for r in app.routes if getattr(r, "path", None)}))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import FRONTEND_DIR
from app.routes.frontend_routes import router as frontend_router
from app.routes.chat_routes import router as chat_router
from app.routes.file_routes import router as file_router

app = FastAPI(title="TCC AI Environment Agent")

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

from app.routes.workspace_routes import router as workspace_router

app.include_router(frontend_router)
app.include_router(chat_router)
app.include_router(file_router)
app.include_router(workspace_router)

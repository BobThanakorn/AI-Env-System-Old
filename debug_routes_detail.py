from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import FRONTEND_DIR
from app.routes.frontend_routes import router as frontend_router

app = FastAPI()
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.include_router(frontend_router)

for route in app.routes:
    print(type(route).__name__, getattr(route, "path", None), getattr(route, "methods", None), getattr(route, "routes", None) and len(route.routes))

import traceback

try:
    from app.core import config
    print("config OK", config.FRONTEND_DIR)
except Exception as e:
    print("config FAIL", e)
    traceback.print_exc()

try:
    from app.routes.frontend_routes import router
    print("frontend_routes OK", [r.path for r in router.routes])
except Exception as e:
    print("frontend_routes FAIL", e)
    traceback.print_exc()

try:
    from app.routes.file_routes import router as file_router
    print("file_routes OK", [r.path for r in file_router.routes])
except Exception as e:
    print("file_routes FAIL", e)
    traceback.print_exc()

try:
    from app.main import app
    print("app routes:", sorted({getattr(r, "path", None) for r in app.routes if getattr(r, "path", None)}))
except Exception as e:
    print("app.main FAIL", e)
    traceback.print_exc()

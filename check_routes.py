import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

checks = {
    "GET /": client.get("/").status_code,
    "GET /chat": client.get("/chat").status_code,
    "GET /create-file": client.get("/create-file").status_code,
    "GET /health": client.get("/health").status_code,
    "POST /files/create": client.post(
        "/files/create",
        json={"filename": "_check.txt", "content": "ok"},
    ).status_code,
}

print("Endpoint checks:")
failed = False
for name, status in checks.items():
    ok = status == 200
    print(f"  {name}: {status} {'OK' if ok else 'FAIL'}")
    if not ok:
        failed = True

if failed:
    sys.exit(1)

print("\nAll endpoint checks passed.")

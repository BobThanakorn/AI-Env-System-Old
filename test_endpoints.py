from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

for path in ["/", "/chat", "/create-file", "/health"]:
    response = client.get(path)
    print(f"GET {path} -> {response.status_code}")

response = client.post(
    "/files/create",
    json={"filename": "route_test.txt", "content": "hello from test"},
)
print(f"POST /files/create -> {response.status_code} {response.json()}")

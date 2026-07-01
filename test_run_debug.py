import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(r"C:\Users\Thanakorn Boonsa-ard\Downloads\TCC Project\workspace")
script = WORKSPACE / "scripts" / "Hello.py"
script.parent.mkdir(parents=True, exist_ok=True)
script.write_text('print("Hello World")\n', encoding="utf-8")

print("executable:", sys.executable)
print("script:", script)

r = subprocess.run(
    [sys.executable, str(script)],
    cwd=str(WORKSPACE),
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)

print("returncode:", r.returncode, hex(r.returncode & 0xFFFFFFFF))
print("stdout:", repr(r.stdout))
print("stderr:", repr(r.stderr))

# Also try -u flag
r2 = subprocess.run(
    [sys.executable, "-u", str(script)],
    cwd=str(WORKSPACE),
    capture_output=True,
    text=True,
)
print("with -u returncode:", r2.returncode)
print("with -u stdout:", repr(r2.stdout))

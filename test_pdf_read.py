import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.config import WORKSPACE_DIR
from app.runtime.upload_context import message_refers_to_upload
from app.tools.file_reader import _read_pdf, read_file_content
from app.tools.file_tools import read_file

assert message_refers_to_upload("read uploaded file then summarize it")
assert message_refers_to_upload("สรุปไฟล์ที่แนบให้หน่อย")

with patch("pypdf.PdfReader") as mock_reader:
    page = MagicMock()
    page.extract_text.return_value = "Internship certificate sample text"
    mock_reader.return_value.pages = [page]

    content, error = _read_pdf(Path("sample.pdf"))
    assert error is None
    assert "Internship certificate" in content

txt_path = WORKSPACE_DIR / "sessions" / "test-read" / "upload" / "note.txt"
txt_path.parent.mkdir(parents=True, exist_ok=True)
txt_path.write_text("Uploaded text file content", encoding="utf-8")

relative = str(txt_path.relative_to(WORKSPACE_DIR)).replace("\\", "/")
result = read_file(relative)
assert "Uploaded text file content" in result["content"]

txt_path.unlink()
print("File read tests passed.")

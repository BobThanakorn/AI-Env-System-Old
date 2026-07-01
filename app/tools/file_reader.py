from pathlib import Path

MAX_READ_CHARS = 16000

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".html",
    ".xml",
    ".log",
    ".yaml",
    ".yml",
}


def _read_pdf(path: Path) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "PDF support is not installed on the server (missing pypdf)."

    try:
        reader = PdfReader(str(path))
        parts: list[str] = []

        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                parts.append(f"--- Page {index} ---\n{page_text}")

        text = "\n\n".join(parts).strip()
        if not text:
            return (
                "",
                "Could not extract text from this PDF. It may be a scanned/image-only PDF. "
                "Try uploading a text-searchable PDF, or convert it to .txt/.docx first.",
            )

        return text[:MAX_READ_CHARS], None
    except Exception as error:
        return "", f"Failed to read PDF: {error}"


def read_file_content(path: Path) -> dict:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        content, error = _read_pdf(path)
        return {
            "format": "pdf",
            "content": content,
            "error": error,
            "truncated": len(content) >= MAX_READ_CHARS,
        }

    if suffix in TEXT_EXTENSIONS or suffix == "":
        content = path.read_text(encoding="utf-8", errors="replace").strip()
        if not content and path.stat().st_size > 0:
            return {
                "format": "binary",
                "content": "",
                "error": (
                    f"Unsupported or binary file type ({suffix or 'unknown'}). "
                    "Supported: .txt, .md, .csv, .json, .pdf"
                ),
                "truncated": False,
            }

        return {
            "format": "text",
            "content": content[:MAX_READ_CHARS],
            "error": None,
            "truncated": len(content) > MAX_READ_CHARS,
        }

    # Last attempt: treat small files as text, otherwise reject.
    size_bytes = path.stat().st_size
    if size_bytes <= 512 * 1024:
        content = path.read_text(encoding="utf-8", errors="replace").strip()
        if content and sum(ch.isprintable() or ch in "\n\r\t" for ch in content) / max(len(content), 1) > 0.85:
            return {
                "format": "text",
                "content": content[:MAX_READ_CHARS],
                "error": None,
                "truncated": len(content) > MAX_READ_CHARS,
            }

    return {
        "format": suffix.lstrip(".") or "binary",
        "content": "",
        "error": (
            f"Unsupported file type ({suffix}). "
            "Supported uploads for reading: .pdf, .txt, .md, .csv, .json"
        ),
        "truncated": False,
    }

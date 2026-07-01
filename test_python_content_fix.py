from app.runtime.python_content import extract_python_from_message, is_valid_python, resolve_python_content

USER_MESSAGE = 'สร้างไฟล์ Hello.py เนื้อหา print("Hello World") แล้วให้แสดงผลลัพธ์ที่ได้ออกมา'
BAD_CONTENT = 'print(" Hello World\\)'
GOOD_CONTENT = 'print("Hello World")'

assert extract_python_from_message(USER_MESSAGE) == 'print("Hello World")'
assert is_valid_python(GOOD_CONTENT)
assert not is_valid_python(BAD_CONTENT)

resolved, meta = resolve_python_content(BAD_CONTENT, USER_MESSAGE)
assert resolved == 'print("Hello World")'
assert meta["content_source"] == "user_message_fallback"

from app.tools.file_tools import write_python

result = write_python("Hello.py", resolved, run=True)
assert result["run_result"]["exit_code"] == 0
assert "Hello World" in result["run_result"]["stdout"]

print("Python content fix tests passed.")

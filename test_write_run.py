from app.tools.file_tools import write_python

result = write_python("Hello2.py", 'print("Hello World")', run=True)
print("status:", result.get("status"))
print("exit:", result.get("run_result", {}).get("exit_code"))
print("stdout:", repr(result.get("run_result", {}).get("stdout")))
print("stderr:", repr(result.get("run_result", {}).get("stderr")))

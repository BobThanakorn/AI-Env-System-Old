from app.core.token_usage import TokenUsage

usage = TokenUsage()
usage.add(100, 50, 150)
usage.add(200, 80, 280)

result = usage.to_dict()
assert result["input_tokens"] == 300
assert result["output_tokens"] == 130
assert result["total_tokens"] == 430
assert result["calls"] == 2

print("Token usage unit tests passed.")

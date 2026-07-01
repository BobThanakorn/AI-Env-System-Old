from typing import Any

from openai import OpenAI

from app.core.config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_BASE_URL, AZURE_OPENAI_MODEL


def get_client() -> OpenAI:
    return OpenAI(
        base_url=AZURE_OPENAI_BASE_URL,
        api_key=AZURE_OPENAI_API_KEY,
    )


def _extract_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if not usage:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    return {
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        "total_tokens": getattr(usage, "total_tokens", 0) or 0,
    }


def _create_response(client: OpenAI, messages: list[dict[str, str]], max_tokens: int, with_reasoning: bool):
    kwargs: dict[str, Any] = {
        "model": AZURE_OPENAI_MODEL,
        "input": messages,
        "max_output_tokens": max_tokens,
    }
    if with_reasoning:
        kwargs["reasoning"] = {"effort": "medium"}

    return client.responses.create(**kwargs)


def call_azure_ai(messages: list[dict[str, str]], max_tokens: int = 2048) -> tuple[str, dict[str, int]]:
    client = get_client()

    try:
        response = _create_response(client, messages, max_tokens, with_reasoning=True)
        return response.output_text or "", _extract_usage(response)

    except Exception as first_error:
        error_text = str(first_error).lower()

        should_retry_without_reasoning = (
            "reasoning" in error_text
            or "unsupported" in error_text
            or "unknown parameter" in error_text
            or "not supported" in error_text
            or "requested operation is unsupported" in error_text
        )

        if not should_retry_without_reasoning:
            raise

        response = _create_response(client, messages, max_tokens, with_reasoning=False)
        return response.output_text or "", _extract_usage(response)

from dataclasses import dataclass, field


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    details: list[dict] = field(default_factory=list)

    def add(self, input_tokens: int, output_tokens: int, total_tokens: int | None = None) -> None:
        total = total_tokens if total_tokens is not None else input_tokens + output_tokens
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += total
        self.calls += 1
        self.details.append(
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total,
            }
        )

    def add_from_dict(self, usage: dict) -> None:
        self.add(
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
            usage.get("total_tokens"),
        )

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
        }

"""Provider-agnostic LLM layer.

``LiteLLMLLM`` talks to any provider LiteLLM supports. ``ScriptedLLM`` is a
deterministic stand-in used by the test suite and offline demos — no network.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Sequence, Union

Messages = Sequence[dict]


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


class BaseLLM:
    """Interface every LLM backend implements."""

    def complete(self, messages: Messages) -> LLMResponse:  # pragma: no cover
        raise NotImplementedError


class LiteLLMLLM(BaseLLM):
    """Real backend. Imports ``litellm`` lazily so the package stays importable
    (and testable) without it installed."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet",
        temperature: float = 0.0,
        max_retries: int = 2,
        retry_base_delay: float = 0.5,
        **kwargs,
    ):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.kwargs = kwargs

    def complete(self, messages: Messages) -> LLMResponse:
        import time

        import litellm

        resp = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = litellm.completion(
                    model=self.model,
                    messages=list(messages),
                    temperature=self.temperature,
                    **self.kwargs,
                )
                break
            except Exception:
                # Retry transient provider/network errors with exponential backoff.
                if attempt >= self.max_retries:
                    raise
                time.sleep(self.retry_base_delay * (2 ** attempt))
        content = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        try:
            cost = float(litellm.completion_cost(completion_response=resp) or 0.0)
        except Exception:
            cost = 0.0
        return LLMResponse(content, prompt_tokens, completion_tokens, cost)


class ScriptedLLM(BaseLLM):
    """Deterministic backend for tests and offline demos.

    Pass a list of canned response strings (returned in order) or a callable
    ``fn(messages) -> str``.
    """

    def __init__(self, responses: Union[Sequence[str], Callable[[Messages], str]], cost_per_call: float = 0.0):
        if callable(responses):
            self._fn: Callable[[Messages], str] | None = responses
            self._queue: List[str] | None = None
        else:
            self._fn = None
            self._queue = list(responses)
        self.cost_per_call = cost_per_call
        self.calls: List[list] = []

    def complete(self, messages: Messages) -> LLMResponse:
        self.calls.append(list(messages))
        if self._fn is not None:
            content = self._fn(messages)
        else:
            assert self._queue is not None
            if not self._queue:
                raise RuntimeError("ScriptedLLM ran out of scripted responses")
            content = self._queue.pop(0)
        return LLMResponse(content=content, cost_usd=self.cost_per_call)

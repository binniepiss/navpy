"""Cost and step budgets that stop runaway agent loops."""
from __future__ import annotations

from dataclasses import dataclass


class BudgetExceeded(Exception):
    """Raised when an agent exhausts its step or cost budget."""


@dataclass
class Budget:
    """Track and enforce a hard cap on steps and spend for a single run."""

    max_steps: int = 20
    max_cost_usd: float = 0.50
    steps: int = 0
    cost_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def tick(self) -> int:
        """Advance one step. Raises :class:`BudgetExceeded` past the cap."""
        self.steps += 1
        if self.steps > self.max_steps:
            raise BudgetExceeded(f"step budget exceeded: {self.steps} > {self.max_steps}")
        return self.steps

    def add_cost(self, amount: float) -> float:
        """Record LLM spend. Raises :class:`BudgetExceeded` past the cap."""
        self.cost_usd += max(0.0, float(amount or 0.0))
        if self.cost_usd > self.max_cost_usd:
            raise BudgetExceeded(f"cost budget exceeded: ${self.cost_usd:.4f} > ${self.max_cost_usd:.4f}")
        return self.cost_usd

    def add_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> int:
        """Record token usage for the run. Returns the running total."""
        self.prompt_tokens += int(prompt_tokens or 0)
        self.completion_tokens += int(completion_tokens or 0)
        return self.total_tokens

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def remaining_steps(self) -> int:
        return max(0, self.max_steps - self.steps)

    def snapshot(self) -> dict:
        return {
            "steps": self.steps,
            "max_steps": self.max_steps,
            "cost_usd": round(self.cost_usd, 6),
            "max_cost_usd": self.max_cost_usd,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

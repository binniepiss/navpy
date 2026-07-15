"""Per-run markdown logging: every step's action, reasoning, and budget."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional


class RunLogger:
    """Append a human-readable markdown trace of a run.

    Set ``run_dir=None`` to keep the log in memory only (``.render()``).
    """

    def __init__(self, run_dir: Optional[str] = None, enabled: bool = True):
        self.enabled = enabled
        self.lines: list[str] = []
        self.path: Optional[str] = None
        if enabled and run_dir:
            os.makedirs(run_dir, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            self.path = os.path.join(run_dir, f"navpy_run_{stamp}.md")
        self._emit(f"# navpy run — {datetime.now(timezone.utc).isoformat()}")

    def _emit(self, line: str) -> None:
        if not self.enabled:
            return
        self.lines.append(line)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def log_step(self, step: int, action, observation: str, page, budget) -> None:
        if not self.enabled:
            return
        self._emit(f"\n## Step {step}")
        self._emit(f"- **page:** {getattr(page, 'url', '')} — {getattr(page, 'title', '')}")
        self._emit(
            f"- **action:** `{action.action}`"
            + (f" element=`{action.element_id}`" if action.element_id else "")
            + (f" value=`{action.value}`" if action.value else "")
        )
        if action.reasoning:
            self._emit(f"- **reasoning:** {action.reasoning}")
        if observation:
            self._emit(f"- **observation:** {observation}")
        self._emit(f"- **budget:** {budget.snapshot()}")

    def render(self) -> str:
        return "\n".join(self.lines)

"""The main navpy Agent: an LLM-driven observe -> act -> extract loop."""
from __future__ import annotations

import json
from typing import Optional, Type

from pydantic import BaseModel, ValidationError

from .actions import execute_action, parse_action
from .budget import Budget
from .dom import PlaywrightBrowser
from .llm import BaseLLM, LiteLLMLLM
from .logging_utils import RunLogger


class NavpyError(Exception):
    """Raised when a run ends without producing valid structured output."""


SYSTEM_PROMPT = """You are navpy, a precise web-automation agent.

Each turn you receive a compact JSON "page graph" describing the interactive
elements on the current web page (each with a stable id like el_003), plus the
user's TASK and an EXTRACTION SCHEMA (JSON Schema).

Respond with EXACTLY ONE JSON action object and nothing else. Valid actions:
  {"action": "click", "element_id": "el_003", "reasoning": "..."}
  {"action": "type", "element_id": "el_001", "value": "text", "reasoning": "..."}
  {"action": "scroll", "direction": "down"}
  {"action": "goto", "url": "https://..."}
  {"action": "extract", "data": { ...must satisfy the EXTRACTION SCHEMA... }}
  {"action": "done"}

Rules:
- Take one small step at a time. Prefer clicking/typing over guessing.
- Only emit "extract" once the requested information is actually visible.
- The "data" object MUST validate against the EXTRACTION SCHEMA.
- If an observation reports an error, choose a different strategy.
"""


class Agent:
    def __init__(
        self,
        model: str = "claude-3-5-sonnet",
        llm: Optional[BaseLLM] = None,
        max_steps: int = 20,
        max_cost_usd: float = 0.50,
        browser=None,
        logger: Optional[RunLogger] = None,
        verbose: bool = False,
    ):
        self.llm = llm or LiteLLMLLM(model=model)
        self.max_steps = max_steps
        self.max_cost_usd = max_cost_usd
        self._browser = browser
        self.logger = logger
        self.verbose = verbose

    def _build_messages(self, task, schema, page, history):
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"TASK:\n{task}\n\nEXTRACTION SCHEMA (JSON Schema):\n{schema_json}"},
        ]
        messages.extend(history[-8:])
        messages.append({"role": "user", "content": f"CURRENT PAGE:\n{page.to_prompt()}"})
        return messages

    def run(self, url: str, task: str, schema: Type[BaseModel], browser=None):
        """Drive the browser to complete ``task`` and return a validated
        ``schema`` instance."""
        browser = browser or self._browser
        owns_browser = browser is None
        if owns_browser:
            browser = PlaywrightBrowser().start()

        budget = Budget(self.max_steps, self.max_cost_usd)
        history: list[dict] = []
        try:
            browser.goto(url)
            while True:
                budget.tick()
                page = browser.serialize()
                messages = self._build_messages(task, schema, page, history)
                response = self.llm.complete(messages)
                budget.add_tokens(response.prompt_tokens, response.completion_tokens)
                budget.add_cost(response.cost_usd)
                action = parse_action(response.content)

                if self.verbose:
                    print(f"[navpy] step {budget.steps}: {action.action} {action.element_id or ''}")
                if self.logger:
                    self.logger.log_step(budget.steps, action, "", page, budget)

                if action.action == "extract":
                    try:
                        return schema(**(action.data or {}))
                    except ValidationError as exc:
                        history.append({"role": "assistant", "content": response.content})
                        history.append({
                            "role": "user",
                            "content": f"Extraction failed schema validation:\n{exc}\nEmit a corrected extract action.",
                        })
                        continue

                if action.action == "done":
                    raise NavpyError("agent emitted 'done' before a valid extract")

                observation = execute_action(browser, action)
                history.append({"role": "assistant", "content": response.content})
                history.append({"role": "user", "content": f"Observation: {observation}"})
        finally:
            if owns_browser:
                browser.close()

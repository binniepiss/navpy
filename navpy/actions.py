"""Action schema, tolerant parser, and executor."""
from __future__ import annotations

import json
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class Action(BaseModel):
    action: Literal["click", "type", "scroll", "goto", "extract", "done"]
    element_id: Optional[str] = None
    value: Optional[str] = None
    direction: Optional[str] = None
    url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None


class ActionError(Exception):
    """Raised when an action cannot be executed against the browser."""


def _extract_json_object(text: str) -> dict:
    """Pull the first JSON object out of an LLM response, tolerating code fences
    and surrounding prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        newline = text.find("\n")
        if newline != -1 and text[:newline].strip().lower() in ("json", ""):
            text = text[newline + 1:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"no JSON object found in model output: {text[:200]!r}")
    return json.loads(text[start:end + 1])


def parse_action(raw: str) -> Action:
    """Parse a raw LLM response string into a validated :class:`Action`."""
    return Action(**_extract_json_object(raw))


def execute_action(browser, action: Action) -> str:
    """Execute a non-terminal action against a browser adapter. ``extract`` and
    ``done`` are terminal and handled by the agent."""
    kind = action.action
    if kind == "click":
        if not action.element_id:
            raise ActionError("click requires element_id")
        return browser.click(action.element_id)
    if kind == "type":
        if not action.element_id:
            raise ActionError("type requires element_id")
        return browser.type(action.element_id, action.value or "")
    if kind == "scroll":
        return browser.scroll(action.direction or "down")
    if kind == "goto":
        if not action.url:
            raise ActionError("goto requires url")
        return browser.goto(action.url)
    raise ActionError(f"not an executable action: {kind}")

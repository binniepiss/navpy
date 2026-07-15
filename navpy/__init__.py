"""navpy — LLM-guided browser automation.

Point it at any URL, describe what you want in plain English, and get back
structured, schema-validated JSON.
"""
from .agent import Agent, NavpyError
from .llm import BaseLLM, LiteLLMLLM, ScriptedLLM, LLMResponse
from .dom import serialize_html, PageGraph, Element, PlaywrightBrowser
from .budget import Budget, BudgetExceeded
from .actions import Action, parse_action, execute_action, ActionError
from .logging_utils import RunLogger

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "NavpyError",
    "BaseLLM",
    "LiteLLMLLM",
    "ScriptedLLM",
    "LLMResponse",
    "serialize_html",
    "PageGraph",
    "Element",
    "PlaywrightBrowser",
    "Budget",
    "BudgetExceeded",
    "Action",
    "parse_action",
    "execute_action",
    "ActionError",
    "RunLogger",
    "__version__",
]

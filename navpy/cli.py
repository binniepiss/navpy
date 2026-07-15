"""navpy command line interface.

    navpy run --url URL --task "..."      # free-form structured extraction
    navpy install                         # install the Playwright browser
    navpy version
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from pydantic import BaseModel, ConfigDict

from . import __version__


class FreeForm(BaseModel):
    """Permissive schema for CLI runs — accepts whatever the model extracts."""

    model_config = ConfigDict(extra="allow")


def _cmd_run(args: argparse.Namespace) -> int:
    from .agent import Agent

    agent = Agent(model=args.model, max_steps=args.max_steps, max_cost_usd=args.max_cost)
    result = agent.run(url=args.url, task=args.task, schema=FreeForm)
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    return 0


def _cmd_install(_args: argparse.Namespace) -> int:
    return subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"])


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"navpy {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="navpy", description="LLM-guided browser automation.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a task against a URL")
    run.add_argument("--url", required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--model", default="claude-3-5-sonnet")
    run.add_argument("--max-steps", type=int, default=20, dest="max_steps")
    run.add_argument("--max-cost", type=float, default=0.50, dest="max_cost")
    run.set_defaults(func=_cmd_run)

    install = sub.add_parser("install", help="install the Playwright chromium browser")
    install.set_defaults(func=_cmd_install)

    version = sub.add_parser("version", help="print version")
    version.set_defaults(func=_cmd_version)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

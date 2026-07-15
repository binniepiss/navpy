# navpy

**LLM-guided browser automation.** Point it at any URL, describe what you want in
plain English, and get back structured, schema-validated JSON.

[![PyPI](https://img.shields.io/pypi/v/navpy.svg)](https://pypi.org/project/navpy/)
[![Python](https://img.shields.io/pypi/pyversions/navpy.svg)](https://pypi.org/project/navpy/)
[![CI](https://github.com/binniepiss/navpy/actions/workflows/ci.yml/badge.svg)](https://github.com/binniepiss/navpy/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

```python
from navpy import Agent
from pydantic import BaseModel

class CompanyInfo(BaseModel):
    name: str
    company_number: str
    registered_address: str
    incorporation_date: str

agent = Agent(model="claude-3-5-sonnet")

result: CompanyInfo = agent.run(
    url="https://find-and-update.company-information.service.gov.uk",
    task="Search for 'Anthropic UK', open the top result, and extract its "
         "registered address and incorporation date.",
    schema=CompanyInfo,
)
print(result.model_dump_json(indent=2))
```

## Why navpy

Every AI team wants agentic browser automation. Skyvern, Browser Use, and
Browserbase are all valued in the hundreds of millions building exactly this.
`navpy` is the clean, minimal, **Python-only** version:

- **~500 lines of readable Python** — not React + Postgres + a SaaS backend.
- **Pydantic-first.** You define the output schema; navpy validates against it and
  re-prompts the model on validation failure until the data is well-formed.
- **Local-model friendly.** Anything [LiteLLM](https://github.com/BerriAI/litellm)
  supports works — OpenAI, Anthropic, or local Qwen / Llama / DeepSeek via Ollama
  or OpenRouter.
- **Runs locally.** No account, no hosted service.
- **Hard cost + step budgets** so a runaway loop can't drain your API balance.

## How it works

```
  goto(url) -> serialize DOM to a compact "page graph"
           -> ask the LLM for ONE JSON action
           -> execute it with Playwright
           -> repeat until `extract` (validated) or budget exhausted
```

1. **DOM chunker** (`dom.py`) strips scripts/styles and extracts interactive
   elements into a small JSON graph (~5-15k tokens) with stable ids.
2. **Action loop** (`agent.py`) sends the graph + task + schema and gets back a
   single action: `click`, `type`, `scroll`, `goto`, `extract`, or `done`.
3. **Extraction** is validated against your Pydantic model; on failure the model
   sees the validation error and retries.
4. **Budget** (`budget.py`) caps `max_steps` (default 20) and `max_cost_usd`
   (default $0.50).

## Install

```bash
pip install navpy
navpy install        # installs the Playwright chromium browser
export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY, etc.
```

## CLI

```bash
navpy run --url https://news.ycombinator.com \
          --task "extract the titles and links of the top 5 stories"
```

## UK / European use cases (see `examples/`)

- Companies House company & filing extraction
- Rightmove / Zoopla property listings
- Reed / Indeed job scraping with structured output
- Generic form fill + confirmation read-back

## Differentiators

| | navpy | Skyvern | Browser Use | Browserbase |
|---|---|---|---|---|
| Python-only | yes | no (React+PG) | yes | no |
| Pydantic schema enforcement | yes | partial | no | no |
| Local models | yes (any LiteLLM) | no | partial | no |
| Runs locally, no account | yes | yes | yes | no (SaaS) |

## Development

```bash
pip install -e ".[dev]"
pytest        # the suite runs fully offline (scripted LLM + fake browser)
```

## License

MIT

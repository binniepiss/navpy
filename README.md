# navpy

navpy is a small Python library for LLM-guided browser automation: point it at a
URL, describe the task in plain English, and it drives a real browser and returns
structured, schema-validated JSON.

I built it because I kept needing to pull structured data off UK sites (Companies
House, Rightmove, job boards) without hand-writing a new scraper each time — and I
wanted the output validated against a schema I define, not best-effort text.

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

## What it does

- **Plain-English tasks in, structured JSON out.** You define a Pydantic schema;
  navpy validates against it and re-prompts the model on validation failure until
  the data is well-formed.
- **Python-only, ~500 lines.** No hosted service, no account — it runs locally.
- **Model-agnostic.** Anything [LiteLLM](https://github.com/BerriAI/litellm)
  supports works — OpenAI, Anthropic, or local Qwen / Llama / DeepSeek via Ollama
  or OpenRouter.
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

navpy isn't published to PyPI yet — install from source:

```bash
git clone https://github.com/binniepiss/navpy
cd navpy
pip install -e .
python -m playwright install chromium   # one-time browser download
export ANTHROPIC_API_KEY=...            # or OPENAI_API_KEY, etc.
```

## CLI

```bash
navpy run --url https://news.ycombinator.com \
  --task "extract the titles and links of the top 5 stories"
```

## Examples (see `examples/`)

- Companies House company & filing extraction
- Rightmove / Zoopla property listings
- Reed / Indeed job scraping with structured output
- Generic form fill + confirmation read-back

## Development

```bash
pip install -e ".[dev]"
pytest        # the suite runs fully offline (scripted LLM + fake browser)
```

## License

MIT

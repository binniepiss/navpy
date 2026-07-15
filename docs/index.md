# navpy documentation

`navpy` turns natural-language tasks into structured data scraped from live web
pages, using any LiteLLM-supported model to drive a Playwright browser.

## Core objects

### `Agent`

```python
Agent(model="claude-3-5-sonnet", llm=None, max_steps=20, max_cost_usd=0.50,
      browser=None, logger=None, verbose=False)
```

`Agent.run(url, task, schema)` drives the browser and returns a validated
instance of `schema` (a Pydantic `BaseModel`).

Inject `llm=` (any `BaseLLM`) or `browser=` to unit-test without a network or a
real browser — see `tests/`.

### `serialize_html(html, url="", title="") -> PageGraph`

Pure function that converts an HTML string into a compact `PageGraph`.

### `Budget(max_steps=20, max_cost_usd=0.50)`

Enforces hard caps; raises `BudgetExceeded`.

## Using a local model

```python
from navpy import Agent
agent = Agent(model="ollama/qwen2.5:72b")   # or openrouter/..., etc.
```

## Logging

Pass `logger=RunLogger(run_dir="runs")` to write a markdown trace of every step.

"""Turn a Reed job search into structured JSON — handy for a personal job tracker.

Requires:  pip install navpy && navpy install
           export ANTHROPIC_API_KEY=...  (or any LiteLLM-supported model)
"""
from pydantic import BaseModel

from navpy import Agent


class Job(BaseModel):
    title: str
    company: str
    location: str
    salary: str
    url: str


class JobSearch(BaseModel):
    query: str
    jobs: list[Job]


def main() -> None:
    # Works with local models too, e.g. model="ollama/qwen2.5:72b".
    agent = Agent(model="claude-3-5-sonnet", max_steps=18, max_cost_usd=0.60)
    result: JobSearch = agent.run(
        url="https://www.reed.co.uk",
        task=(
            "Search for 'graduate data analyst' jobs in London and extract the "
            "first 8 results with title, company, location, salary, and URL."
        ),
        schema=JobSearch,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

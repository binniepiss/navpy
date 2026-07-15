"""Extract a company's details from Companies House by natural-language task.

Requires:  pip install navpy && navpy install
           export ANTHROPIC_API_KEY=...
"""
from pydantic import BaseModel

from navpy import Agent


class CompanyFiling(BaseModel):
    date: str
    document_type: str
    url: str


class CompanyInfo(BaseModel):
    name: str
    company_number: str
    registered_address: str
    incorporation_date: str
    filings: list[CompanyFiling]


def main() -> None:
    agent = Agent(model="claude-3-5-sonnet", max_steps=15, max_cost_usd=0.50)
    result: CompanyInfo = agent.run(
        url="https://find-and-update.company-information.service.gov.uk",
        task=(
            "Search for 'Anthropic UK', open the top result, and extract the "
            "company's registered address, incorporation date, and last 3 filings."
        ),
        schema=CompanyInfo,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

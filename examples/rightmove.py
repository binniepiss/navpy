"""Scrape structured property listings from a Rightmove search.

Requires:  pip install navpy && navpy install
           export OPENAI_API_KEY=...
"""
from pydantic import BaseModel

from navpy import Agent


class Listing(BaseModel):
    address: str
    price_pcm: str
    bedrooms: int
    url: str


class SearchResults(BaseModel):
    location: str
    listings: list[Listing]


def main() -> None:
    agent = Agent(model="gpt-4.1", max_steps=20, max_cost_usd=0.75)
    result: SearchResults = agent.run(
        url="https://www.rightmove.co.uk",
        task=(
            "Search for 2-bedroom flats to rent in Camden, London and extract the "
            "first 5 listings with address, monthly price, bedrooms, and listing URL."
        ),
        schema=SearchResults,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

"""End-to-end agent test with a scripted LLM and a fake browser — no network."""
from pydantic import BaseModel

from navpy import Agent, ScriptedLLM, serialize_html

SEARCH_PAGE = """
<html><head><title>Companies House</title></head><body>
  <input type="search" name="q" aria-label="Search companies">
  <button type="submit">Search</button>
  <a href="/company/12345">Anthropic UK Ltd</a>
</body></html>
"""

COMPANY_PAGE = """
<html><head><title>Anthropic UK Ltd</title></head><body>
  <h1>Anthropic UK Ltd</h1>
  <p>Company number 12345678</p>
  <a href="/">Back</a>
</body></html>
"""


class FakeBrowser:
    def __init__(self, pages, start_url):
        self.pages = pages
        self.url = start_url
        self.events = []

    def goto(self, url):
        self.url = url
        return f"goto {url}"

    def serialize(self):
        return serialize_html(self.pages[self.url], url=self.url)

    def click(self, element_id):
        self.events.append(("click", element_id))
        el = self.serialize().by_id(element_id)
        if el and el.href:
            self.url = el.href
        return f"clicked {element_id}"

    def type(self, element_id, value):
        self.events.append(("type", element_id, value))
        return f"typed {value} into {element_id}"

    def scroll(self, direction):
        self.events.append(("scroll", direction))
        return f"scrolled {direction}"

    def close(self):
        pass


class CompanyInfo(BaseModel):
    name: str
    company_number: str


def test_agent_runs_search_then_extracts():
    browser = FakeBrowser({"/": SEARCH_PAGE, "/company/12345": COMPANY_PAGE}, start_url="/")
    llm = ScriptedLLM([
        '{"action": "type", "element_id": "el_001", "value": "Anthropic"}',
        '{"action": "click", "element_id": "el_002"}',
        '{"action": "click", "element_id": "el_003"}',
        '{"action": "extract", "data": {"name": "Anthropic UK Ltd", "company_number": "12345678"}}',
    ], cost_per_call=0.001)

    agent = Agent(llm=llm, browser=browser, max_steps=10, max_cost_usd=1.0)
    result = agent.run(url="/", task="Find Anthropic UK and extract its number", schema=CompanyInfo)

    assert isinstance(result, CompanyInfo)
    assert result.name == "Anthropic UK Ltd"
    assert result.company_number == "12345678"
    assert ("type", "el_001", "Anthropic") in browser.events
    assert browser.url == "/company/12345"


def test_agent_recovers_from_bad_extract():
    browser = FakeBrowser({"/": COMPANY_PAGE}, start_url="/")
    llm = ScriptedLLM([
        '{"action": "extract", "data": {"name": "Anthropic UK Ltd"}}',
        '{"action": "extract", "data": {"name": "Anthropic UK Ltd", "company_number": "12345678"}}',
    ])
    agent = Agent(llm=llm, browser=browser, max_steps=10)
    result = agent.run(url="/", task="extract", schema=CompanyInfo)
    assert result.company_number == "12345678"
    assert len(llm.calls) == 2

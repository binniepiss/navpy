"""DOM chunker / serializer.

Turns raw HTML into a compact "page graph" — a small JSON-serialisable list of
interactive elements with stable ids. ``serialize_html`` is pure and fully
unit-testable with no browser. ``PlaywrightBrowser`` is the live adapter.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import List, Optional

INTERACTIVE_TAGS = ["a", "button", "input", "select", "textarea"]


@dataclass
class Element:
    id: str
    tag: str
    type: Optional[str] = None
    text: Optional[str] = None
    aria_label: Optional[str] = None
    href: Optional[str] = None
    placeholder: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, "")}


@dataclass
class PageGraph:
    url: str = ""
    title: str = ""
    elements: List[Element] = field(default_factory=list)
    text: str = ""

    def by_id(self, element_id: str) -> Optional[Element]:
        for el in self.elements:
            if el.id == element_id:
                return el
        return None

    def to_prompt(self, max_elements: int = 120, max_text: int = 2000) -> str:
        payload = {
            "url": self.url,
            "title": self.title,
            "elements": [e.to_dict() for e in self.elements[:max_elements]],
            "visible_text": self.text[:max_text],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)


def _clean(text: Optional[str]) -> str:
    return " ".join((text or "").split())


def serialize_html(html: str, url: str = "", title: str = "") -> PageGraph:
    """Parse an HTML string into a :class:`PageGraph`.

    Interactive elements are numbered el_001, el_002, ... in document order,
    matching ``document.querySelectorAll`` so live selectors line up.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for junk in soup(["script", "style", "noscript"]):
        junk.decompose()

    if not title and soup.title and soup.title.string:
        title = _clean(soup.title.string)

    elements: List[Element] = []
    for i, node in enumerate(soup.find_all(INTERACTIVE_TAGS), start=1):
        elements.append(
            Element(
                id=f"el_{i:03d}",
                tag=node.name,
                type=node.get("type"),
                text=_clean(node.get_text()) or None,
                aria_label=node.get("aria-label"),
                href=node.get("href"),
                placeholder=node.get("placeholder"),
                name=node.get("name"),
                value=node.get("value"),
            )
        )

    return PageGraph(url=url, title=title, elements=elements, text=_clean(soup.get_text(" ")))


_ANNOTATE_JS = """
() => {
  const els = document.querySelectorAll('a,button,input,select,textarea');
  let i = 1;
  els.forEach((el) => {
    el.setAttribute('data-navpy-id', 'el_' + String(i).padStart(3, '0'));
    i += 1;
  });
  return document.documentElement.outerHTML;
}
"""


class PlaywrightBrowser:
    """Live browser adapter backed by Playwright (imported lazily)."""

    def __init__(self, headless: bool = True, timeout_ms: int = 15000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser = None
        self.page = None

    def start(self) -> "PlaywrightBrowser":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self.page = self._browser.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        return self

    def goto(self, url: str) -> str:
        self.page.goto(url)
        return f"navigated to {url}"

    def serialize(self) -> PageGraph:
        html = self.page.evaluate(_ANNOTATE_JS)
        return serialize_html(html, url=self.page.url, title=self.page.title())

    def click(self, element_id: str) -> str:
        self.page.click(f'[data-navpy-id="{element_id}"]')
        self.page.wait_for_load_state("networkidle")
        return f"clicked {element_id}"

    def type(self, element_id: str, value: str) -> str:
        self.page.fill(f'[data-navpy-id="{element_id}"]', value)
        return f"typed {value!r} into {element_id}"

    def scroll(self, direction: str = "down") -> str:
        delta = 800 if direction != "up" else -800
        self.page.mouse.wheel(0, delta)
        return f"scrolled {direction}"

    def close(self) -> None:
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()

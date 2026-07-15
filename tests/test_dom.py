from navpy import serialize_html

SAMPLE = """
<html><head><title>Companies House</title></head>
<body>
  <h1>Search the register</h1>
  <input type="search" name="q" aria-label="Search companies" placeholder="Company name">
  <button type="submit">Search</button>
  <ul>
    <li><a href="/company/12345">Anthropic UK Ltd</a></li>
    <li><a href="/company/67890">Anthropic Holdings Ltd</a></li>
  </ul>
  <script>console.log('tracking')</script>
</body></html>
"""


def test_title_and_element_count():
    page = serialize_html(SAMPLE, url="https://example.com")
    assert page.title == "Companies House"
    assert len(page.elements) == 4


def test_stable_ids_in_document_order():
    page = serialize_html(SAMPLE)
    assert [e.id for e in page.elements] == ["el_001", "el_002", "el_003", "el_004"]


def test_element_attributes_captured():
    page = serialize_html(SAMPLE)
    search = page.by_id("el_001")
    assert search.tag == "input"
    assert search.type == "search"
    assert search.aria_label == "Search companies"
    assert search.placeholder == "Company name"
    link = page.by_id("el_003")
    assert link.href == "/company/12345"
    assert link.text == "Anthropic UK Ltd"


def test_scripts_stripped_from_text():
    page = serialize_html(SAMPLE)
    assert "tracking" not in page.text
    assert "Search the register" in page.text


def test_to_prompt_is_compact_json():
    page = serialize_html(SAMPLE)
    prompt = page.to_prompt()
    assert '"el_001"' in prompt
    assert "tracking" not in prompt

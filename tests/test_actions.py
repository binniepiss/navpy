import pytest

from navpy import parse_action, execute_action, ActionError


class RecordingBrowser:
    def __init__(self):
        self.events = []

    def click(self, element_id):
        self.events.append(("click", element_id))
        return f"clicked {element_id}"

    def type(self, element_id, value):
        self.events.append(("type", element_id, value))
        return f"typed into {element_id}"

    def scroll(self, direction):
        self.events.append(("scroll", direction))
        return f"scrolled {direction}"

    def goto(self, url):
        self.events.append(("goto", url))
        return f"goto {url}"


def test_parse_plain_json():
    action = parse_action('{"action": "click", "element_id": "el_002"}')
    assert action.action == "click"
    assert action.element_id == "el_002"


def test_parse_fenced_json_with_prose():
    raw = "Sure!\n```json\n{\"action\": \"type\", \"element_id\": \"el_001\", \"value\": \"hi\"}\n```"
    action = parse_action(raw)
    assert action.action == "type"
    assert action.value == "hi"


def test_parse_extract_with_nested_data():
    action = parse_action('{"action": "extract", "data": {"name": "Acme", "n": 3}}')
    assert action.action == "extract"
    assert action.data == {"name": "Acme", "n": 3}


def test_parse_no_json_raises():
    with pytest.raises(ValueError):
        parse_action("there is no json here")


def test_execute_click_and_type():
    browser = RecordingBrowser()
    execute_action(browser, parse_action('{"action": "click", "element_id": "el_002"}'))
    execute_action(browser, parse_action('{"action": "type", "element_id": "el_001", "value": "x"}'))
    assert browser.events == [("click", "el_002"), ("type", "el_001", "x")]


def test_execute_terminal_action_raises():
    with pytest.raises(ActionError):
        execute_action(RecordingBrowser(), parse_action('{"action": "done"}'))

"""Read and fill lab script elements by id, preserving all surrounding HTML."""

import json
from html.parser import HTMLParser


class _ScriptParser(HTMLParser):
    def __init__(self, html, element_id):
        super().__init__(convert_charrefs=False)
        self.element_id = element_id
        self.line_offsets = [0]
        for line in html.split("\n"):
            self.line_offsets.append(self.line_offsets[-1] + len(line) + 1)
        self.matches = []
        self.open_script = None
        self.feed(html)
        self.close()

    def source_offset(self):
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id") != self.element_id:
            return
        if tag != "script":
            raise ValueError(f"{self.element_id} must be a script element")
        start = self.source_offset() + len(self.get_starttag_text())
        self.open_script = (start, attributes)

    def handle_endtag(self, tag):
        if tag == "script" and self.open_script is not None:
            start, attributes = self.open_script
            self.matches.append((start, self.source_offset(), attributes))
            self.open_script = None


def _script_span(html, element_id, expected_type):
    parser = _ScriptParser(html, element_id)
    if len(parser.matches) != 1 or parser.open_script is not None:
        raise ValueError(f"Expected exactly one complete script element with id {element_id}")
    start, end, attributes = parser.matches[0]
    if attributes.get("type", "") != expected_type:
        raise ValueError(f"Unexpected script type for {element_id}")
    return start, end


def read_page_data(html):
    start, end = _script_span(html, "lab-data", "application/json")
    return json.loads(html[start:end])


def fill_page_data(html, data):
    start, end = _script_span(html, "lab-data", "application/json")
    # HTML ends even a non-executable script at </script>, including inside JSON strings.
    payload = json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    return html[:start] + payload + html[end:]


def append_page_script(html, code):
    """Keep the comparison bridge in the viewer's executable script and scope."""
    _, end = _script_span(html, "lab-script", "")
    return html[:end] + code + html[end:]

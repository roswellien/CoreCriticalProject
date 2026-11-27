"""Add Open Graph and Twitter card tags to every built page.

Discord, X, Reddit, Slack and others read these tags to draw a link preview. Doing it
at build time covers the hand-written pages and the generated news/media/mech pages
alike, from each page's own <title> and description, so no page can be forgotten.
"""

import re
from pathlib import Path

SITE_URL = "https://corecritical.dev"
IMAGE_PATH = "/assets/plates/og-image.jpg"
IMAGE_ALT = (
    "The Core Critical MW3 wordmark beside the classic Mad Cat in an amber-lit hangar."
)
SITE_NAME = "Core Critical"

TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.DOTALL)
DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+name="description"\s+content="([^"]*)"', re.DOTALL
)
NOINDEX_PATTERN = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex')


def page_url(page_path):
    """The address Cloudflare Pages serves a page at: no .html, index as its folder."""
    url_path = page_path.as_posix()
    if url_path == "index.html":
        return SITE_URL + "/"
    if url_path.endswith("/index.html"):
        return f"{SITE_URL}/{url_path[: -len('index.html')]}"
    return f"{SITE_URL}/{url_path.removesuffix('.html')}"


def social_tags(title, description, url):
    # title and description come from the page's own markup, so they are already
    # HTML-escaped text that is safe inside a double-quoted attribute.
    tags = [
        ("property", "og:type", "website"),
        ("property", "og:site_name", SITE_NAME),
        ("property", "og:title", title),
        ("property", "og:url", url),
        ("property", "og:image", SITE_URL + IMAGE_PATH),
        ("property", "og:image:width", "1200"),
        ("property", "og:image:height", "630"),
        ("property", "og:image:alt", IMAGE_ALT),
        ("name", "twitter:card", "summary_large_image"),
        ("name", "twitter:title", title),
        ("name", "twitter:image", SITE_URL + IMAGE_PATH),
        ("name", "twitter:image:alt", IMAGE_ALT),
    ]
    if description:
        tags.insert(3, ("property", "og:description", description))
        tags.append(("name", "twitter:description", description))
    return "".join(f'<meta {kind}="{key}" content="{value}" />' for kind, key, value in tags)


def add_social_tags(dist):
    """Insert the tags before </head> in each page under dist; return pages changed."""
    changed = 0
    for page in sorted(Path(dist).rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        already_tagged = 'property="og:image"' in html
        hidden_from_search = NOINDEX_PATTERN.search(html) is not None
        title_match = TITLE_PATTERN.search(html)
        if already_tagged or hidden_from_search or title_match is None or "</head>" not in html:
            continue
        title = " ".join(title_match.group(1).split()).replace('"', "&quot;")
        description_match = DESCRIPTION_PATTERN.search(html)
        description = ""
        if description_match is not None:
            description = " ".join(description_match.group(1).split())
        url = page_url(page.relative_to(dist))
        tags = social_tags(title, description, url)
        page.write_text(html.replace("</head>", tags + "</head>", 1), encoding="utf-8")
        changed += 1
    return changed

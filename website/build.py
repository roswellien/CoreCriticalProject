"""Build the static site and its development news from docs/mechlab."""
from datetime import date
from html import escape
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
OUT.mkdir(exist_ok=True)
site_files = (
    "index.html",
    "styles.css",
    "site.js",
    "projects.html",
    "news.html",
    "media.html",
    "about.html",
    "project.html",
    "404.html",
)
for name in site_files:
    if name == "index.html":
        continue
    source = ROOT / name
    if source.is_file():
        shutil.copy2(source, OUT / name)
shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)

def read_news_entry(path: Path) -> tuple[date, str, str] | None:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.md", path.name)
    if not match:
        return None
    published = date.fromisoformat(match.group(1))
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next(
        (line.removeprefix("# ").strip() for line in lines if line.startswith("# ")),
        path.stem,
    )
    paragraph_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(stripped)
    summary = " ".join(paragraph_lines)
    if len(summary) > 280:
        summary = summary[:280].rsplit(" ", 1)[0].rstrip(" .") + "…"
    return published, title, summary


news_directory = ROOT.parent / "docs" / "mechlab"
entries = [
    entry
    for path in news_directory.glob("????-??-??.md")
    if (entry := read_news_entry(path))
]
entries.sort(key=lambda entry: entry[0], reverse=True)
news_rows = "\n".join(
    '<article class="news-entry"><time datetime="{0}">{1}</time>'
    '<h2 id="news-{0}">{2}</h2><p>{3}</p></article>'.format(
        published.isoformat(), published.strftime("%d %b %Y"), escape(title), escape(summary)
    )
    for published, title, summary in entries
)
home_rows = "\n".join(
    '<a class="update-row" href="news.html#news-{0}"><time datetime="{0}">{1}</time>'
    '<div><h3>{2}</h3><p>{3}</p></div></a>'.format(
        published.isoformat(), published.strftime("%d %b %Y"), escape(title), escape(summary)
    )
    for published, title, summary in entries[:2]
)
news_page = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<title>Development news | Core Critical</title>'
    '<link rel="stylesheet" href="styles.css"></head>'
    '<body><header class="site-header"><a class="brand" href="index.html">'
    '<span>CORE CRITICAL</span></a><nav class="primary-nav" aria-label="Main navigation">'
    '<a href="index.html">Home</a><a href="projects.html">Projects</a>'
    '<a href="news.html" aria-current="page">News</a><a href="media.html">Media</a>'
    '<a href="about.html">About</a><a href="https://github.com/roswellien/MW3Recomp">GitHub</a>'
    '</nav></header><main id="main" class="section-shell"><h1>Development news</h1>{rows}</main></body></html>'
).format(rows=news_rows)
(OUT / "news.html").write_text(news_page, encoding="utf-8")
index_source = (ROOT / "index.html").read_text(encoding="utf-8")
updates_section = re.compile(r'<section class="updates section-shell".*?</section>', re.DOTALL)
index_source, replacement_count = updates_section.subn(
    '<section class="updates section-shell" aria-labelledby="updates-title">'
    '<div class="section-heading">'
    '<h2 id="updates-title">From the development floor</h2>'
    '<a class="text-link" href="news.html">All updates</a></div>'
    + home_rows
    + '</section>',
    index_source,
    count=1,
)
if replacement_count != 1:
    raise ValueError("Homepage must contain exactly one development updates section")
(OUT / "index.html").write_text(index_source, encoding="utf-8")
print(f"Static preview ready: {OUT}")

"""Copy the portable site into dist; keep design notes and tools private."""
from pathlib import Path
import shutil
from tools.render_mechlab import render_site
from tools.render_media import render_media
from tools.sync_mechlab import read_notes

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
OUT.mkdir(exist_ok=True)
site_files = (
    "index.html",
    "styles.css",
    "site.js",
    "projects.html",
    "news.html",
    "projects.html",
    "media.html",
    "about.html",
    "native.html",
    "vulkan.html",
    "tools.html",
    "project.html",
    "404.html",
)
for name in site_files:
    source = ROOT / name
    if source.is_file():
        shutil.copy2(source, OUT / name)
shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
notes = read_notes(ROOT.parent / "docs" / "mechlab", ROOT.parent)
render_site(ROOT, OUT, notes)
render_media(ROOT, OUT)
print(f"Static preview ready: {OUT}")

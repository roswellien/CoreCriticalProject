"""Copy the portable site into dist; keep design notes and tools private."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
OUT.mkdir(exist_ok=True)
for name in ("index.html", "styles.css", "site.js", "projects.html", "news.html", "media.html", "about.html", "project.html", "404.html"):
    source = ROOT / name
    if source.is_file():
        shutil.copy2(source, OUT / name)
shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
print(f"Static preview ready: {OUT}")

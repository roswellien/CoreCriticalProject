"""Copy the portable site into dist; keep design notes and tools private."""
from pathlib import Path
import shutil
from tools.render_mechlab import render_site
from tools.render_media import render_media
from tools.sync_mechlab import read_notes

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
OUT.mkdir(exist_ok=True)
for name in ("index.html", "styles.css", "site.js", "news.html", "media.html", "about.html", "native.html", "vulkan.html", "tools.html", "studio-tour.html", "404.html"):
    source = ROOT / name
    if source.is_file():
        shutil.copy2(source, OUT / name)
shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
repository_root = ROOT.parent
notes = read_notes(repository_root / "docs" / "mechlab", repository_root)
render_site(ROOT, OUT, notes)
render_media(ROOT, OUT)
# Alias /studio/ to studio-tour.html as well for direct access
studio_dir = OUT / "studio"
studio_dir.mkdir(exist_ok=True)
tour_file = OUT / "studio-tour.html"
if tour_file.is_file():
    shutil.copy2(tour_file, studio_dir / "index.html")
print(f"Static preview ready: {OUT}")

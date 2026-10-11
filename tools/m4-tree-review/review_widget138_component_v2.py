"""Schema repair of the retained independent component review; no candidate edits."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_widget138_component.py')
source=p.read_text()
assert source.count("p['copied_generated_files']")==1
source=source.replace("p['copied_generated_files']","p['prior_copy_relations']")
exec(compile(source,str(Path(__file__)), 'exec'), globals())

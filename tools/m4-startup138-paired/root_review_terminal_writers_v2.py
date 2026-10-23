"""Use the PE reader's requested length, not its section backing-end value."""
from pathlib import Path
p=Path(__file__).with_name('root_review_terminal_writers_v1.py');s=p.read_text()
a="image.data[start:end].hex()";b="image.read(start,10).hex()";assert s.count(a)==1;s=s.replace(a,b)
assert s.count('widget-terminal-writer-root-review-r1')==1;s=s.replace('widget-terminal-writer-root-review-r1','widget-terminal-writer-root-review-r2')
s=s.replace('pin(__file__);value=',"pin(__file__);pin(Path(__file__).with_name('root_review_terminal_writers_v1.py'));value=")
exec(compile(s,str(p),'exec'))

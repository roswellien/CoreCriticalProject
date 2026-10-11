"""Retain failed exact CPU comparison and add complete mismatch diagnostics."""
from pathlib import Path
p=Path(__file__).with_name('compare_original_game_v2.py');q=p.with_name('compare_original_game_v3.py');assert not q.exists();s=p.read_text();a="'Every NULL-free source-derived CPU GPR/flags/PC at actual entry/RET'";assert s.count(a)==1;s=s.replace(a,a+"+str((hex(entry),hex(self.cursor),cpu,list(words(r,32,10))))");q.write_text(s)

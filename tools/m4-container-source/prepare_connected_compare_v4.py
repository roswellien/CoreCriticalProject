"""Use sealed full FS descriptor entry field (distinct minimal helper_entry)."""
from pathlib import Path
p=Path(__file__).with_name('compare_connected_v3.py');q=p.with_name('compare_connected_v4.py');assert not q.exists();s=p.read_text();a="f['helper_entry']";assert s.count(a)==1;q.write_text(s.replace(a,"f['entry']"))

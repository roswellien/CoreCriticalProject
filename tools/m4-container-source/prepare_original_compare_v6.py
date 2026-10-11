"""Use actual shim return field; Cpu.pc is explicitly unpopulated in API ledger."""
from pathlib import Path
p=Path(__file__).with_name('compare_original_game_v5.py');q=p.with_name('compare_original_game_v6.py');assert not q.exists();s=p.read_text();a="fact[25]==0x78001385 and fact[19]==0x78001385";assert s.count(a)==1;s=s.replace(a,"fact[25]==0x78001385 and fact[19]==0");q.write_text(s)

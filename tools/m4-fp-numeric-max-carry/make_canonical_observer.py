"""New author narrow-domain observer; frozen model source remains unchanged."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'tools/m4-fp-numeric-max-host-boundary/observe.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f910489a7d77c6585280be4d3ffceb7c489b0f5b91b577c2179e129c1f7f9472'
s=p.read_text().replace("ROOT/'reports/m4-fp-numeric-max-host-boundary'", "ROOT/'reports/m4-fp-numeric-max-carry'")
s=s.replace("'unit-O0/schema.json'", "'legacy-unit-O0/schema.json'").replace("f'unit-{level}/persistent.bin'", "f'legacy-unit-{level}/persistent.bin'").replace("f'replay-{mode}-{level}/replay.bin'", "f'legacy-replay-{mode}-{level}/replay.bin'")
out=Path(__file__).with_name('observe_canonical_legacy.py');assert not out.exists();out.write_text(s)

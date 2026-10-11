"""Correct the packed Sample's post-call CPU offset; preserve failed v5."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v5.py';s=p.read_text();a="reader.data('sample.bin')[8800:8840]";assert s.count(a)==1;s=s.replace(a,"reader.data('sample.bin')[8840:8880]")
target=R/'tools/m4-formatting-source/compare_native_fixture_v6.py';assert not target.exists();target.write_text(s)

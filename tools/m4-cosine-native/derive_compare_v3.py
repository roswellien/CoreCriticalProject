"""Additive observation-record ordering repair; comparisons are unchanged."""
from pathlib import Path
source = (Path(__file__).parent / 'compare_v2.py').read_text()
before = "                observations[-1]['host_FX_raw_differences'] = [dict(offset=i, before=a, after=b)\n                    for i, (a, b) in enumerate(zip(host0, host1)) if a != b]\n                observations[-1]['whole_host_FX512_equality_claimed'] = False"
after = "                host_differences = [dict(offset=i, before=a, after=b)\n                    for i, (a, b) in enumerate(zip(host0, host1)) if a != b]"
assert source.count(before) == 1
source = source.replace(before, after)
before = "                                         XOR_AF_semantic_equality_claimed=False, full_State_source_comparison=False))"
after = "                                         host_FX_raw_differences=host_differences, whole_host_FX512_equality_claimed=False,\n                                         XOR_AF_semantic_equality_claimed=False, full_State_source_comparison=False))"
assert source.count(before) == 1
source = source.replace(before, after)
target = Path(__file__).parent / 'compare_v3.py'
assert not target.exists()
target.write_text(source)

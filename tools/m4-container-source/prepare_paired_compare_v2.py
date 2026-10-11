"""Bind final normal FS source witness derivative; preserve initial policy tool."""
from pathlib import Path
p=Path(__file__).with_name('compare_paired_policy.py');q=p.with_name('compare_paired_policy_v2.py');assert not q.exists();s=p.read_text();q.write_text(s.replace('connected-native-source-r3','connected-native-source-r4'))

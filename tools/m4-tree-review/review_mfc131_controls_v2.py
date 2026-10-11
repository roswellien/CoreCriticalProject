"""Normalize only JSON tuple representation for whole unique proof equality.

The first audit completed all actual byte comparisons. Its final physical
proof equality compared in-memory tuples against serialized JSON lists. This
derivative retains every check and normalizes that one JSON representation.
"""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
parent = ROOT / 'tools/m4-tree-review/review_mfc131_controls.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest() == '3ad23a6e49aaab8c3a5dfbefdfb4ddd3f867f12f60b62dcebb6d5c4695107ebc'
text = parent.read_text()
old = "eq(list(proofs.values()), read(Path(source_path).parent / 'unique-physical-API-proofs.json'),"
new = "eq(json.loads(json.dumps(list(proofs.values()))), read(Path(source_path).parent / 'unique-physical-API-proofs.json'),"
assert text.count(old) == 1
text = text.replace(old, new)
old = 'pin(__file__); pin(sys.executable)'
assert text.count(old) == 1
text = text.replace(old, "pin(__file__); pin(parent); pin(sys.executable)")
exec(compile(text, str(parent), 'exec'), globals())

"""Reuse the accepted corpus builder for the new frozen130 schedule."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).resolve().parents[1] / 'm4-joint-startup125/build.py'
text = parent.read_text().replace('startup125', 'startup130').replace('connected125', 'connected130').replace('changed125', 'changed130')
marker = " sources[str(Path(__file__).resolve())]=sha(__file__)"
assert text.count(marker) == 1
text = text.replace(marker, marker + "\n sources[str(ROOT/'tools/m4-joint-startup125/build.py')]=sha(ROOT/'tools/m4-joint-startup125/build.py')")
exec(compile(text, str(parent), 'exec'), globals())

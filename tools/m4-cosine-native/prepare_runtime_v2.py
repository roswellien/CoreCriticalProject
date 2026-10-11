"""Qualify borrowed cosine TLS frame against the fixed protocol frame."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('prepare_runtime.py')
text = parent.read_text()
before = ' frame=runtime.cpu().esp;sentinel=runtime.memory().load<unsigned>({frame});'
after = ' m4_fp_compound_native::frame=runtime.cpu().esp;m4_fp_compound_native::sentinel=runtime.memory().load<unsigned>({m4_fp_compound_native::frame});'
assert text.count(before) == 1
text = text.replace(before, after)
text = text.replace('    pin(__file__)', "    pin(__file__)\n    pin(Path(__file__).with_name('prepare_runtime.py'))")
exec(compile(text, str(parent), 'exec'), globals())

"""Retain failed r1; use corrected Runtime TLS and a real copied retry FX."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('prepare_runtime_fixture.py')
text = parent.read_text()
text = text.replace("'runtime-preparation-r1/report.json'", "'runtime-preparation-r2/report.json'")
text = text.replace('d6c804c83b1f9a00fb026a27d0df1d6982d93d63f133d214956354d8bcf7c506',
                    '6b9ad4a06fc8426b8c7215cd31a118883e8de7c4bc9c7087647ebe0c017fd61e')
before = '  const auto retry_cpu=c.runtime().cpu(),retry_fx=c.runtime().fx();'
after = '  const auto retry_cpu=c.runtime().cpu();std::array<std::byte,512>retry_fx{};std::copy(c.runtime().fx().begin(),c.runtime().fx().end(),retry_fx.begin());'
assert text.count(before) == 1
text = text.replace(before, after)
text = text.replace('retry_fx==c.runtime().fx()', '!std::memcmp(retry_fx.data(),c.runtime().fx().data(),512)')
text = text.replace('    pin(__file__)', "    pin(__file__)\n    pin(Path(__file__).with_name('prepare_runtime_fixture.py'))")
exec(compile(text, str(parent), 'exec'), globals())

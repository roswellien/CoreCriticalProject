"""Identity-only repair; preserve the failed first preparation unchanged."""
from pathlib import Path
import hashlib
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).with_name('prepare_inputs.py')
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == 'c83a28afc1ee0883d4af46a2e9a893922927da03522aa291d09a779e0065c21c'
source = BASE.read_text(encoding='utf-8')
old = '2ef1668832203026a9796fda9415a5955b9d917e6d42ea0b9a76e33cd9c28f41'
new = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
assert source.count(old) == 1
source = source.replace(old, new)
namespace = {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'}
exec(compile(source, str(BASE), 'exec'), namespace)

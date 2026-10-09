"""Fixed original-BEFORE consumer for the reused heap provider continuation."""
import hashlib
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
path = ROOT/'tools/m4-crt-heap-version-root/consumer.py'
digest = 'b4884e5968dbfbb99809f1d5dfaac314c76c5ecbdb4ad360abb5a1b131d72b83'
if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
    raise ValueError('Frozen original-BEFORE version-query consumer')
spec = importlib.util.spec_from_file_location('heap_return_fixed_consumer', path)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
F, M, OLD, STATE_REG = prior.F, prior.M, prior.OLD, prior.STATE_REG
F.pin(path, digest)

"""Fixed original-BEFORE consumer; no candidate expectations."""
import hashlib
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
path=ROOT/'tools/m4-crt-heap-mode-root/consumer.py'
digest='b48ca5c27029b1639e477e369394b6c81f94e256fb8e0d5bf589b3168506a783'
if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
    raise ValueError('Frozen original-BEFORE heap-mode consumer')
spec=importlib.util.spec_from_file_location('heap_version_fixed_consumer',path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
F,M,OLD,STATE_REG=prior.F,prior.M,prior.OLD,prior.STATE_REG
F.pin(path,digest)

"""Reuse the fixed original-BEFORE consumer, without candidate expectations."""
import importlib.util
import hashlib
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
path = ROOT/'tools/m4-crt-heap-create-root/consumer.py'
digest = '47e1f69819a8f94b05a670c5f3cbd97edbbf03808dff6f499d74359723986b82'
if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
    raise ValueError('Frozen heap-creation original-BEFORE consumer')
spec = importlib.util.spec_from_file_location('heap_mode_frozen_consumer',path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
F,M,OLD,STATE_REG = prior.F,prior.M,prior.OLD,prior.STATE_REG
F.pin(path,digest)

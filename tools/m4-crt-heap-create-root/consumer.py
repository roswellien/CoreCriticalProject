"""Reuse the immutable original-BEFORE consumer implementation."""
import importlib.util
from pathlib import Path
import hashlib
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
path = ROOT/'tools/m4-crt-heap-init-root/consumer.py'
if hashlib.sha256(path.read_bytes()).hexdigest() != '01c0c248f00785acb73b5c1ce96f2ddda1b675db6c60a0602bf04c175b1b48a8':
    raise ValueError('Frozen original-BEFORE consumer')
spec = importlib.util.spec_from_file_location('heap_create_frozen_consumer', path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
F, M, OLD, STATE_REG = old.F, old.M, old.OLD, old.STATE_REG
F.pin(path, '01c0c248f00785acb73b5c1ce96f2ddda1b675db6c60a0602bf04c175b1b48a8')

"""Carry the exact original BEFORE and declared lower page; no AFTER seeds."""
import importlib.util
from consumer import F

path = F.pin(F.ROOT/'tools/m4-crt-heap-version-root/before.py',
    'eb99d9298b3fd81d405d193b311b2379abc47ea55d0c73c011d26a5e5ee7f8d2')
spec = importlib.util.spec_from_file_location('heap_return_fixed_before', path)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
PAGE, PROBE_PAGE, STACK_PAGE = prior.PAGE, prior.PROBE_PAGE, prior.STACK_PAGE
SELECTOR, PROBE, COLD_PAGE, SPANS = prior.SELECTOR, prior.PROBE, prior.COLD_PAGE, prior.SPANS
stage, expected = prior.stage, prior.expected

"""Frozen original-BEFORE startup seam with additional literal source identities."""
import importlib.util
import types
from consumer import F

path = F.pin(F.ROOT/'tools/m4-crt-locale-default-root/before.py',
    '9776d1271e1076990f7f50d264eae54f88d332cb6b817197c444fb7db7ceb830')
spec = importlib.util.spec_from_file_location('heap_frozen_mainargs_seam', path)
OLD_BEFORE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OLD_BEFORE)


def stage(state, fx, cpu, memory):
    value = OLD_BEFORE.stage(state, fx, cpu, memory)
    value['heap-fragment.bin'] = bytes(memory[0x78001000][0x83c:0x843])
    value['heap-provider.bin'] = bytes(memory[0x78003000][0x9bf:0xa0c])
    return value


# Only the stage observation grows. This frozen source interpreter still
# derives the healthy seam from the original BEFORE, not candidate AFTER bytes.
expected = types.FunctionType(OLD_BEFORE.expected.__code__,
    dict(OLD_BEFORE.expected.__globals__, stage=stage))

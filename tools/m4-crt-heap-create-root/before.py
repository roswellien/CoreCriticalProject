"""Derive the authentic startup seam with one additional raw RW data page."""
import importlib.util
import types
from consumer import F, M, OLD

path = F.pin(F.ROOT/'tools/m4-crt-heap-init-root/before.py',
    '59d30086da10be4dcb20b9c0bd9dc2016264b871f02b688e59eabda89a74b70a')
spec = importlib.util.spec_from_file_location('heap_create_frozen_before', path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
PAGE = 0x78035000


def stage(state, fx, cpu, memory):
    value = prior.stage(state, fx, cpu, memory)
    value['page-'+str(PAGE)+'.bin'] = bytes(memory[PAGE])
    return value


def expected(row, payload, wp, pp, gp, program, providers, maths, ctrl,
             init, args, argv, source, level='O0'):
    def memory(*values):
        result = OLD.base_memory(*values)
        result[0x78003000] = bytearray(source[0x78003000])
        result[PAGE] = bytearray(source[PAGE])
        return result

    writer = types.FunctionType(F.writer.__code__,
        dict(F.writer.__globals__, base_memory=memory, stage=stage))
    frozen = prior.OLD_BEFORE
    predict = types.FunctionType(OLD.expected.__code__,
        dict(OLD.expected.__globals__, M=types.SimpleNamespace(Entry=frozen.LocaleEntry),
             writer_result=writer, stage=stage))
    entry, phases = predict(row, payload, wp, pp, gp, program, providers,
        maths, ctrl, init, args, argv, source, 0, level)
    phases.pop('entry-after-fault')
    phases.pop('retry-after')
    return entry, phases

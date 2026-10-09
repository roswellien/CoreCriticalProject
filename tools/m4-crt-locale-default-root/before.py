"""Original-BEFORE source execution halted at the explicit locale bootstrap seam."""
import types
from consumer import F, M, OLD

PAGE = 0x78003000


def stage(state, fx, cpu, memory):
    result = OLD.stage(state, fx, cpu, memory)
    result['page-'+str(PAGE)+'.bin'] = bytes(memory[PAGE])
    result['commandline-source.bin'] = bytes(memory[0x78001000][0x88c:0x897])
    result['parser-source.bin'] = bytes(memory[0x7800b000][0xc48:0xdfc])
    result['locale-stub.bin'] = bytes(memory[PAGE][0xdd2:0xddb])
    result['locale-setmbcp.bin'] = bytes(memory[PAGE][0xddb:0xe84])
    result['locale-lock.bin'] = bytes(memory[0x78001000][0x55:0xb0])
    return result


class BeforeLocale(Exception):
    pass


class LocaleEntry(M.Entry):
    def args_snapshot(self, tag):
        super().args_snapshot(tag)
        if tag == 'mainargs-before':
            raise BeforeLocale()

    def run(self):
        try:
            super().run()
        except BeforeLocale:
            return self
        raise ValueError('Original source did not reach the declared healthy locale seam')


def expected(row, payload, wp, pp, gp, program, providers, maths, ctrl,
             init, args, argv, source, level='O0'):
    def memory(*values):
        result = OLD.base_memory(*values)
        result[PAGE] = bytearray(source[PAGE])
        return result

    writer = types.FunctionType(F.writer.__code__,
        dict(F.writer.__globals__, base_memory=memory, stage=stage))
    predict = types.FunctionType(OLD.expected.__code__,
        dict(OLD.expected.__globals__, M=types.SimpleNamespace(Entry=LocaleEntry),
             writer_result=writer, stage=stage))
    entry, phases = predict(row, payload, wp, pp, gp, program, providers,
        maths, ctrl, init, args, argv, source, 0, level)
    # The old orchestration's terminal labels are not observed before this new
    # source-qualified bootstrap runs. Its earlier snapshots remain independent.
    phases.pop('entry-after-fault')
    phases.pop('retry-after')
    return entry, phases

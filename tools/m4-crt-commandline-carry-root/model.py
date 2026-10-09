"""BEFORE-derived carried producer model with a declared native OS input.

The seam is an explicitly authored bootstrap invocation of eleven original
bytes. It is not a reconstructed DllMain or a guest RET. No native AFTER State,
CPU or memory is used as an expected-machine seed.
"""
import copy
import struct
import types
from consumer import F, M, OLD

WRITER, RETURN, END = 0x7800188c, 0x78001892, 0x78001897
SLOT, RAW, GLOBAL, BUFFER = 0x7802e034, 0x3442e, 0x78037174, 0x33000000

class CarryEntry(M.Entry):
    def __init__(self, *args, host_bytes, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_bytes = bytes(host_bytes)
        self.cmd_accesses, self.cmd_events, self.cmd_phases = [], [], {}
        self.cmd_owned = False
        if not self.host_bytes or len(self.host_bytes) > 131072 or self.host_bytes[-1] != 0 or 0 in self.host_bytes[:-1]:
            raise ValueError('Actual single bounded NUL-inclusive host input required')

    def cmd_snapshot(self, tag):
        self.cmd_phases[tag] = (bytes(self.state), bytes(self.runtime_cpu),
                                copy.deepcopy(self.mem), bytes(self.fx), self.cmd_owned)

    def args_snapshot(self, tag):
        super().args_snapshot(tag)
        if tag == 'mainargs-before':
            self.produce()

    def produce(self):
        saved_pc = struct.unpack_from('<I', self.state, 2472)[0]
        frame = self.r['esp']
        assert frame == 0x20001860 and self.raw_load(GLOBAL) == 0 and self.raw_load(SLOT) == RAW
        self.cmd_snapshot('commandline-producer-before')
        struct.pack_into('<I', self.state, 2472, WRITER)
        self.cmd_snapshot('commandline-producer-projected')
        self.cmd_accesses.append((WRITER, SLOT, RAW, 4, 0))
        self.raw_store(frame - 4, RETURN)
        self.cmd_accesses.append((WRITER, frame - 4, RETURN, 4, 1))
        self.r['esp'] = frame - 4
        self.project(RAW)
        self.cmd_snapshot('commandline-api-before')
        # The host call only supplies measured ANSI bytes. It contributes no
        # fabricated guest values or x86 API volatile-register equivalence.
        self.cmd_snapshot('commandline-api-after')
        self.cmd_owned = True
        self.cmd_snapshot('commandline-buffer-after')
        self.r['eax'], self.r['esp'] = BUFFER, frame
        self.project(RETURN)
        self.raw_store(GLOBAL, BUFFER)
        self.cmd_accesses.append((RETURN, GLOBAL, BUFFER, 4, 1))
        self.project(END)
        self.cmd_snapshot('commandline-producer-after')
        struct.pack_into('<I', self.state, 2472, saved_pc)
        runtime = bytearray(self.runtime_cpu)
        struct.pack_into('<I', runtime, 0, BUFFER)
        self.runtime_cpu = bytes(runtime)
        self.cmd_snapshot('commandline-carry-after')

def expected(row, payload, wp, pp, gp, program, providers, maths, ctrl,
             init, args, argv, source, host_bytes, level='O0'):
    # Clone only the frozen expectation orchestration; provide an independent
    # subclass and explicit bundle reader. Candidate expected code is absent.
    entry_type = lambda *a, **kw: CarryEntry(*a, host_bytes=host_bytes, **kw)
    facade = types.SimpleNamespace(Entry=entry_type)
    predict = types.FunctionType(OLD.expected.__code__,
        dict(OLD.expected.__globals__, M=facade, writer_result=F.writer))
    entry, phases = predict(row, payload, wp, pp, gp, program, providers,
        maths, ctrl, init, args, argv, source, 0, level)
    for tag, value in entry.cmd_phases.items():
        phases[tag] = OLD.stage(value[0], value[3], value[1], value[2])
    return entry, phases

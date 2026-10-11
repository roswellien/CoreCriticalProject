"""Additive literal fixed-vtable normal source model after accepted116.

Every indirect operand is first read from the actual persistent source page.
The fixed dispatch relation leaves that physical DWORD unchanged. The admitted
59FF80 constructor domain is the original zero argument, so no pointee read is
claimed. No candidate phase state or pages initialize this source machine.
"""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sp = importlib.util.spec_from_file_location('accepted116_fixed_game_model', ROOT/'tools/m4-container-source/game_model.py')
G = importlib.util.module_from_spec(sp)
sp.loader.exec_module(G)
I = G.I
SF = G.SF
begin_root = G.begin_root
complete_root = G.complete_root

def frozen(path, expected):
    raw = (ROOT/path).read_bytes()
    I.need(hashlib.sha256(raw).hexdigest() == expected, 'Exact additive fixed-vtable source input')
    return json.loads(raw)

def source_program():
    program, callbacks = G.source_program()
    data = frozen('reports/m4-next-source/recovery-r1/instruction-contracts.json',
                  'a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108')
    for row in data['instructions']:
        pc = row['pc']
        I.need(pc not in program or program[pc] == row, 'Identical retained/new literal source instruction')
        program[pc] = row
    data = frozen('reports/m4-next-source/game-callbacks-r1/callbacks.json',
                  'f318d7e95dc4c6127fba5b9b91db792a5b32ac1a86fbf02e6a106ed26b209712')
    for pc, offsets in data['State_offsets_by_original_PC'].items():
        pc, offsets = int(pc), tuple(offsets)
        I.need(pc not in callbacks or callbacks[pc] == offsets, 'Identical actual source undefined callback')
        callbacks[pc] = offsets
    return program, callbacks

class Machine(G.Machine):
    def read(self, address, size=4, domain='source', pc=None):
        original_pc = self.word(2472) if pc is None else pc
        value = super().read(address, size, domain, pc)
        if domain == 'source' and size == 4:
            fixed = {(0x59fbab, 0x5cfd14): 0x40e820,
                     (0x59fdc5, 0x5bc100): 0x59ff00,
                     (0x59ff6e, 0x5bc0fc): 0x59ff80}.get((original_pc, address))
            if fixed is not None:
                I.need(value == fixed, 'Exact raw fixed source dispatch DWORD')
                if original_pc in (0x59fbab, 0x59ff6e):
                    I.need(self.bytes(self.reg('esp'), 4) == bytes(4), 'Only genuine zero constructor argument admitted')
                if original_pc == 0x59ff6e:
                    I.need(self.reg('edx') == 0x5bc0e0,
                           'Exact source-established instance vptr before indirect CALL')
        return value

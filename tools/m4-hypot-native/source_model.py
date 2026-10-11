"""Literal finite integer/control model with explicit original FP seams.

Only per-FNSTSW AX16, per-FSTP memory scalars, and final SW/raw80 fields
come from measured numerical observations. No complete AFTER CPU, State,
page, or execution path is supplied to the model or native worker.
"""
import struct

GPR = (2216, 2248, 2264, 2232, 2312, 2328, 2280, 2296)
SF = ((0,2755),(1,2753),(2,2751),(3,2749),(4,2747),(5,2745),
      (6,2757),(8,2737),(9,2739),(10,2741),(14,2743))


def machine_class(I):
    class Numeric(I.Machine):
        def __init__(self, *args, descriptors, numerical_seams, **kwargs):
            super().__init__(*args, **kwargs)
            self.descriptors = descriptors
            self.numerical_seams = numerical_seams
            self.seam_index = 0
            self.used_seams = []
            self.cw = struct.unpack_from('<H', self.state, 2768)[0]
            self.cw_events = []
            self.last_fp = None
            self.last_fp_address = None

        def step(self):
            pc = self.cursor
            row = self.program[pc]
            op, args = row['mnemonic'], row['decoded_operands']
            if not (op.startswith('f') or op in ('wait','movsx','not','sahf')):
                return super().step()
            self.word(2472, pc)
            self.PCs.append(pc)
            self.steps += 1
            self.cursor = pc + row['width']
            if op == 'movsx':
                value = self.operand(args[1])
                bits = args[1]['bits']
                if value & (1 << (bits - 1)):
                    value -= 1 << bits
                self.destination(args[0], value)
            elif op == 'not':
                self.destination(args[0], ~self.operand(args[0]))
            elif op == 'sahf':
                ah = self.reg('ah')
                for flag, bit in (('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7)):
                    self.flag(flag, ah >> bit & 1)
            elif op == 'fnstsw':
                I.need(row['bytes_hex'] == 'dfe0' and args[0]['register'] == 'ax',
                       'Finite literal FNSTSW AX16 seam')
                seam = self.numerical_seams[self.seam_index]
                I.need(seam['kind'] == 'SW_AX16' and seam['PC'] == pc,
                       'Exact current FNSTSW observation identity')
                self.seam_index += 1
                self.reg('ax', seam['value'])
                self.used_seams.append(dict(seam))
            elif op == 'wait':
                I.need(not self.descriptors[pc]['cells'], 'Literal FWAIT has no memory effect')
            else:
                desc = self.descriptors[pc]
                I.need(op in ('fld','fstp','fnstcw','fldcw','fcomp','fxch','fdiv',
                              'fmul','fsub','faddp','fsqrt','fldpi','fdivr'),
                       'Finite admitted literal FP operation')
                for d in desc['cells']:
                    registers = tuple(self.reg(n) for n in ('eax','ecx','edx','ebx','esp','ebp','esi','edi'))
                    I.need(not d['segment'], 'Actual flat source FP operand')
                    address = (d['displacement'] + sum(v*c for v,c in zip(registers,d['coefficients']))) & 0xffffffff
                    I.need(bool(d['read']) != bool(d['write']), 'Exclusive finite FP read/write operand')
                    width = d['width']
                    if d['read']:
                        value = self.read(address, width)
                        if op == 'fldcw':
                            I.need(width == 2, 'Literal FLDCW word operand')
                            self.cw = value
                            self.cw_events.append(dict(PC=pc, address=address, value=value))
                    else:
                        if op == 'fnstcw':
                            I.need(width == 2, 'Literal FNSTCW word operand')
                            value = self.cw
                        else:
                            I.need(op == 'fstp' and width in (4,8), 'Only finite FSTP scalar numerical write seam')
                            seam = self.numerical_seams[self.seam_index]
                            I.need((seam['kind'],seam['PC'],seam['address'],seam['width']) ==
                                   ('FSTP_SCALAR',pc,address,width), 'Exact current source scalar seam identity')
                            self.seam_index += 1
                            value = int.from_bytes(bytes.fromhex(seam['bytes_hex']), 'little')
                            self.used_seams.append(dict(seam))
                        self.write(address, value, width)
                if op not in ('fnstcw','fldcw'):
                    self.last_fp = row
                    self.last_fp_address = address if desc['cells'] else None
            for offset in self.callbacks.get(pc, ()):
                self.state[offset] = 0
                self.undefined.append((pc,offset,0))

        def project_final_fp(self, observed_sw, observed_raw80):
            """Map limited measured FP fields to the declared native representation."""
            I.need(len(observed_raw80) == 8 and all(len(b) == 10 for b in observed_raw80),
                   'Eight complete finite raw80 fields')
            before_sw = struct.unpack_from('<H', self.state, 2770)[0]
            I.need(observed_sw & 0x3800 == before_sw & 0x3800,
                   'Balanced literal source final TOP')
            for bit, offset in SF:
                self.state[offset] = observed_sw >> bit & 1
            struct.pack_into('<H', self.state, 2768, self.cw)
            struct.pack_into('<H', self.state, 2770, (before_sw & ~0x3800) | (observed_sw & 0x3800))
            for i, raw in enumerate(observed_raw80):
                self.state[2486+i*16:2496+i*16] = raw
            last = self.last_fp
            I.need(last['pc'] == 0x4b5905 and last['mnemonic'] == 'fstp' and
                   last['bytes_hex'] == 'd95e20', 'Physical last FP metadata-defining instruction')
            raw = bytes.fromhex(last['bytes_hex'])
            address = self.last_fp_address
            I.need(address == 0x60b2e8, 'Source-derived final FP data address')
            struct.pack_into('<H', self.state, 2774, ((raw[0]&7)<<8)|raw[1])
            struct.pack_into('<I', self.state, 2776, last['pc'])
            self.state[2780:2782] = self.state[2110:2112]
            struct.pack_into('<I', self.state, 2784, address)
            self.state[2788:2790] = self.state[2106:2108]
            I.need(self.seam_index == len(self.numerical_seams), 'Every finite numerical seam consumed exactly once')
    return Numeric

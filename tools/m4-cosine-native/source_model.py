"""Literal compound source effects with an explicit finite original FP oracle.

The admitted numerical seam contains only the three observed F32 outputs,
original x87 status and raw80 register observations. It never supplies a whole
AFTER CPU, State or page to the native worker or to this reconstruction.
"""
import re
import struct

GPR = (2216, 2248, 2264, 2232, 2312, 2328, 2280, 2296)
AF = ((0, 2065), (2, 2067), (4, 2069), (6, 2071), (7, 2073), (10, 2075), (11, 2077))
SF = ((0, 2755), (1, 2753), (2, 2751), (3, 2749), (4, 2747), (5, 2745),
      (6, 2757), (8, 2737), (9, 2739), (10, 2741), (14, 2743))


def derive(state_before, cpu_before, pages_before, original, contracts, pages):
    assert len(state_before) == 3504 and len(pages_before) == 43 * 4096
    rows = contracts['instructions']
    assert len(rows) == 19 and sum(row['width'] for row in rows) == 110
    assert [row['mnemonic'] for row in rows] == ['jmp', 'fld', 'fcos', 'xor'] + ['mov'] * 7 + ['fstp', 'fld', 'fcos', 'fstp', 'fld', 'fcos', 'fstp', 'ret']
    state = bytearray(state_before)
    memory = bytearray(pages_before)
    cpu = list(cpu_before)
    events = []
    f32_oracles = []

    def offset(address):
        assert address & ~4095 in pages
        return pages.index(address & ~4095) * 4096 + (address & 4095)

    def read(address, width, pc):
        start = offset(address)
        value = int.from_bytes(memory[start:start + width], 'little')
        events.append(dict(pc=pc, address=address, width=width, writing=False, value=value))
        return value

    def write(address, value, width, pc):
        start = offset(address)
        memory[start:start + width] = value.to_bytes(width, 'little')
        events.append(dict(pc=pc, address=address, width=width, writing=True, value=value))

    inputs = {item['address']:bytes.fromhex(item['bytes_hex']) for item in contracts['inputs']}
    for row in rows:
        mnemonic, pc = row['mnemonic'], row['pc']
        if mnemonic == 'xor':
            assert row['operands'] == 'eax, eax'
            cpu[0] = 0
            # CF/PF/ZF/SF/OF are defined by the literal XOR. AF uses the
            # candidate's explicit zero representative, without AF equality credit.
            cpu[8] = (cpu[8] & ~0x8d5) | 0x44
        elif mnemonic == 'ret':
            assert row['bytes_hex'] == 'c3'
            cpu[9] = read(cpu[4], 4, pc)
            cpu[4] += 4
        elif mnemonic in ('mov', 'fld', 'fstp'):
            match = re.search(r'\[(0x[0-9a-f]+)\]', row['operands'])
            assert match
            address = int(match[1], 16)
            if mnemonic == 'fld':
                value = read(address, 8, pc)
                assert value.to_bytes(8, 'little') == inputs[address]
                start = offset(address)
                assert original[2276 + start:2276 + start + 8] == inputs[address]
            elif mnemonic == 'mov':
                operand = row['operands'].split(',')[-1].strip()
                value = cpu[0] if operand == 'eax' else int(operand, 0)
                write(address, value, 4, pc)
            else:
                start = offset(address)
                scalar = original[178404 + start:178404 + start + 4]
                assert len(scalar) == 4
                value = int.from_bytes(scalar, 'little')
                write(address, value, 4, pc)
                f32_oracles.append(dict(pc=pc, address=address, bytes_hex=scalar.hex()))
        else:
            assert mnemonic in ('jmp', 'fcos')
    assert len(events) == 14 and len(f32_oracles) == 3
    for index, at in enumerate(GPR):
        struct.pack_into('<I', state, at, cpu[index])
    struct.pack_into('<I', state, 2472, cpu[9])
    for bit, at in AF:
        state[at] = cpu[8] >> bit & 1
    # This matches the previously accepted finite FP oracle seam. The
    # complete original result is never substituted for reconstructed State.
    fx = original[628:1140]
    sw = struct.unpack_from('<H', fx, 2)[0]
    assert struct.unpack_from('<H', fx)[0] == struct.unpack_from('<H', state_before, 2768)[0]
    assert sw & 0x3800 == struct.unpack_from('<H', state_before, 2770)[0] & 0x3800
    assert not sw & 0x400 and fx[4] == 0
    for bit, at in SF:
        state[at] = sw >> bit & 1
    before_sw = struct.unpack_from('<H', state_before, 2770)[0]
    struct.pack_into('<H', state, 2770, (before_sw & ~0x3800) | (sw & 0x3800))
    for index in range(8):
        state[2486 + index * 16:2496 + index * 16] = fx[32 + index * 16:42 + index * 16]
    last = next(row for row in reversed(rows) if row['mnemonic'] == 'fstp')
    raw = bytes.fromhex(last['bytes_hex'])
    destination = int(re.search(r'\[(0x[0-9a-f]+)\]', last['operands'])[1], 16)
    struct.pack_into('<H', state, 2774, ((raw[0] & 7) << 8) | raw[1])
    struct.pack_into('<I', state, 2776, last['pc'])
    state[2780:2782] = state_before[2110:2112]
    struct.pack_into('<I', state, 2784, destination)
    state[2788:2790] = state_before[2090:2092]
    return dict(state=bytes(state), CPU=tuple(cpu), pages=bytes(memory), events=events,
                numerical_oracle=dict(F32=f32_oracles, original_SW=sw,
                                      raw80_hex=[fx[32 + i * 16:42 + i * 16].hex() for i in range(8)]),
                original_AFTER_machine_seed=False, complete_State_after_copy=False)

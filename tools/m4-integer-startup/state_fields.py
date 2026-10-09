"""Complete checked State projections reused from the frozen first gate."""

import ctypes as c

def rendered(api, value):
    pointer = api.PrintValueToString(value)
    try:
        return c.string_at(pointer).decode()
    finally:
        api.DisposeMessage(pointer)

def state_fields(layouts):
    """Named observations, each derived from the complete LLVM struct proof."""
    x = layouts['struct.X86State']['offsets']
    fields = {}
    def field(name, offset, width, **details):
        fields[name] = {'offset': offset, 'bytes': width, **details}
    gpr = layouts['struct.GPR']['offsets']
    for name, index in {'EAX': 1, 'ECX': 5, 'EDX': 7, 'EBX': 3, 'ESP': 13,
                        'EBP': 15, 'ESI': 9, 'EDI': 11, 'EIP': 33}.items():
        field(name, x[6] + gpr[index] + layouts['struct.Reg']['offsets'][0], 4)
    flags = layouts['struct.ArithFlags']['offsets']
    for name, index in {'CF': 1, 'PF': 3, 'AF': 5, 'ZF': 7, 'SF': 9, 'DF': 11, 'OF': 13}.items():
        field(name, x[2] + flags[index], 1)
    field('vector_storage', x[1], 32 * layouts['union.VectorReg']['size'], count=32, stride=64)
    field('logical_x87_storage', x[7], layouts['struct.X87Stack']['size'], count=8, stride=16)
    for i in range(8):
        field(f'logical_ST{i}_raw80', x[7] + i * layouts['struct.anon.3']['size'] +
              layouts['struct.anon.3']['offsets'][1], layouts['struct.float80_t']['size'])
    field('MMX_storage', x[8], layouts['struct.MMX']['size'], count=8, stride=16)
    for i in range(8):
        field(f'MMX{i}', x[8] + i * layouts['struct.anon.4']['size'] +
              layouts['struct.anon.4']['offsets'][1], 8)
    sw = layouts['struct.FPUStatusFlags']['offsets']
    for name, index in {'C0': 1, 'C1': 3, 'C2': 5, 'C3': 7, 'PE': 9, 'UE': 11,
                        'OE': 13, 'ZE': 15, 'DE': 17, 'IE': 19, 'SF': 21}.items():
        field('x87_' + name, x[9] + sw[index], 1)
    fpu = x[11] + layouts['union.FPU']['offsets'][0] + layouts['struct.anon.11']['offsets'][0]
    fx = layouts['struct.FpuFXSAVE']['offsets']
    for name, index, width in [('CW', 0, 2), ('SW', 1, 2), ('physical_FTW', 2, 1), ('FOP', 4, 2),
                              ('FIP', 5, 4), ('FCS', 6, 2), ('FDP', 8, 4), ('FDS', 9, 2),
                              ('MXCSR', 11, 4), ('MXCSR_MASK', 12, 4)]:
        field('x87_' + name, fpu + fx[index], width)
    fields['x87_TOP'] = {**fields['x87_SW'], 'bit_offset': 11, 'bit_width': 3}
    field('legacy_fxsave_guest_storage', fpu, layouts['union.FPU']['size'])
    return fields

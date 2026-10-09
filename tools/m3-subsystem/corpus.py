"""Authored sequence inputs and exact measurement oracle for two MW3 entries.

No proprietary instruction bytes or executable game implementation are embedded.
Expected results and access events are measurement data, never worker bodies.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import random
import struct

SETTER, CONSUMER, SENTINEL = 0x558290, 0x55A560, 0x10000100
STACK, GLOBAL, BUFFER = 0x20001000, 0x72C000, 0x20003000
PAGE, BUFFER_BYTES, MEMORY_SIZE, STATE_SIZE = 4096, 8192, 16384, 3504
MAX_STEPS, MAX_ROWS, MAX_COLUMNS, MAX_EVENTS = 16, 16, 32, 2048
REQUEST_SIZE, STEP_SIZE, RESULT_SIZE = 1296, 48, 73728
U32, ENTRY_FLAGS, SETTER_FLAGS, CONSUMER_FLAGS = 0xFFFFFFFF, 0xCD5, 0xCC5, 0xCD5
HEADER, PREFIX, STEP, EVENT = (struct.Struct(fmt) for fmt in ("<8s4I", "<4I", "<12I", "<4I"))
IMAGE_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
SETTER_SHA = "fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa"
CONSUMER_SHA = "072fed4d6b5efe0ff7c3bfa1733c848a11f3ba5402fd05d18c2f1ebf8ff57adf"
CWS = tuple(0x7F | pc << 8 | rc << 10 for pc in (0, 2, 3) for rc in range(4))
SEED = 0x340055A560


def signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def truncating_half(value: int) -> int:
    value = signed(value)
    return (value // 2 if value >= 0 else -((-value) // 2)) & U32


def raw80(sig: int, exponent: int) -> bytes:
    return struct.pack("<QH", sig, exponent)


PATTERNS = (
    tuple(raw80(0x8000000000000001 + i * 0x1000000000000002,
                (0xBFFF if i & 1 else 0x3FFF) + i // 2) for i in range(8)),
    (raw80(0, 0), raw80(0, 0x8000), raw80(1 << 63, 0x7FFF), raw80(1 << 63, 0xFFFF),
     raw80(0xC000000000001234, 0x7FFF), raw80(0xC000000000004321, 0xFFFF),
     raw80(0xD000000000005678, 0x7FFF), raw80(0xE00000000000ABCD, 0xFFFF)),
)


def full_tags(fx: bytes) -> int:
    if len(fx) != 512:
        raise ValueError("FX input length")
    top, ftw = (struct.unpack_from("<H", fx, 2)[0] >> 11) & 7, fx[4]
    result = 0
    for logical in range(8):
        sig, exp = struct.unpack_from("<QH", fx, 32 + logical * 16)
        exp &= 0x7FFF
        physical = (top + logical) & 7
        if not ftw & 1 << physical:
            tag = 3
        elif not sig and not exp:
            tag = 1
        elif exp == 0x7FFF and sig >> 63 and (sig == 1 << 63 or sig & 1 << 62):
            tag = 2
        elif 0 < exp < 0x7FFF and sig >> 63:
            tag = 0
        else:
            raise ValueError("Unsupported occupied raw80 encoding")
        result |= tag << (physical * 2)
    return result


def fx_seed(cw: int, top: int, ftw: int, sw: int, pattern: int, seed: int) -> bytes:
    if cw not in CWS or not 0 <= top < 8 or not 0 <= ftw < 256 or sw & ~0x477F:
        raise ValueError("Invalid authored FP seed")
    fx = bytearray(512)
    struct.pack_into("<HH", fx, 0, cw, sw | top << 11)
    fx[4] = ftw
    # This host can erase metadata during descheduling, even across an
    # integer-only interval. Nonzero metadata is outside this measured domain.
    struct.pack_into("<I", fx, 24, 0x1F80)
    for i, value in enumerate(PATTERNS[pattern]):
        fx[32 + i * 16:42 + i * 16] = value
    fx[160:288] = bytes((seed + i * 73 + 0x5B) & 255 for i in range(128))
    return bytes(fx)


@dataclass(frozen=True)
class Operation:
    cpu: tuple[int, ...]
    arg_a: int = 0
    arg_b: int = 0

    def pack(self) -> bytes:
        if len(self.cpu) != 10:
            raise ValueError("CPU field count")
        return STEP.pack(*self.cpu, self.arg_a, self.arg_b)


@dataclass(frozen=True)
class Sequence:
    steps: tuple[Operation, ...]
    seed: int
    tags: int
    fx: bytes
    category: str = "supplied_sequence"

    def pack(self) -> bytes:
        validate_sequence(self)
        return (PREFIX.pack(len(self.steps), self.seed, self.tags, 0) + self.fx +
                b"".join(step.pack() for step in self.steps) +
                bytes((MAX_STEPS - len(self.steps)) * STEP_SIZE))


@dataclass(frozen=True)
class ExpectedStep:
    cpu_before: tuple[int, ...]
    cpu_after: tuple[int, ...]
    memory_before: bytes
    memory_after: bytes
    events: tuple[tuple[int, int, int, int], ...]
    flag_mask: int


def initial_memory(sequence: Sequence) -> bytes:
    stack = bytes((i * 37 + sequence.seed) & 255 for i in range(PAGE))
    buffer = bytes((i * 73 + (sequence.seed >> 8) + (i >> 8) * 19 + 0x5B) & 255
                   for i in range(BUFFER_BYTES))
    return stack + bytes(PAGE) + buffer


def memory_offset(address: int, width: int) -> int:
    if not isinstance(address, int) or not isinstance(width, int) or width <= 0 or not 0 <= address <= U32 or address + width > 1 << 32:
        raise ValueError("Invalid nonwrapping memory span")
    for base, size, offset in ((STACK, PAGE, 0), (GLOBAL, PAGE, PAGE),
                               (BUFFER, BUFFER_BYTES, PAGE * 2)):
        if base <= address and address + width <= base + size:
            return offset + address - base
    raise ValueError("Unmapped operation span")


def buffer_span(address: int, width: int = 2) -> None:
    if not BUFFER <= address or address + width > BUFFER + BUFFER_BYTES:
        raise ValueError("Consumer access outside isolated buffer block")


def validate_fx(sequence: Sequence) -> None:
    fx = sequence.fx
    if len(fx) != 512 or not 0 <= sequence.tags <= 0xFFFF:
        raise ValueError("Invalid FX/full-tag size")
    cw, sw = struct.unpack_from("<HH", fx)
    if cw not in CWS or sw & ~0x7F7F:
        raise ValueError("Unsupported masked control/status input")
    if struct.unpack_from("<H", fx, 6)[0] & ~0x7FF:
        raise ValueError("Invalid FOP metadata")
    if (struct.unpack_from("<H", fx, 6)[0] or
            struct.unpack_from("<I", fx, 8)[0] or
            struct.unpack_from("<I", fx, 16)[0]):
        raise ValueError("Unsupported nonzero guest FOP/FIP/FDP metadata")
    if struct.unpack_from("<2I", fx, 24) != (0x1F80, 0):
        raise ValueError("Unsupported guest MXCSR input")
    for i, byte in enumerate(fx):
        allowed = (i < 5 or 6 <= i < 12 or 16 <= i < 20 or 24 <= i < 32 or
                   32 <= i < 160 and (i - 32) % 16 < 10 or 160 <= i < 288)
        if byte and not allowed:
            raise ValueError("Nonzero FX reserved/selectors")
    if full_tags(fx) != sequence.tags:
        raise ValueError("Incoherent physical FTW/full tags")


def _validate_operation(operation: Operation) -> None:
    if len(operation.cpu) != 10 or any(not isinstance(v, int) or not 0 <= v <= U32
                                    for v in (*operation.cpu, operation.arg_a, operation.arg_b)):
        raise ValueError("Invalid operation integer fields")
    flags, pc, esp = operation.cpu[8], operation.cpu[9], operation.cpu[4]
    if flags & ~(ENTRY_FLAGS | 0x202) or flags & 0x202 != 0x202:
        raise ValueError("Unsafe entry flags")
    if pc == SETTER:
        if not STACK <= esp or esp + 12 > STACK + PAGE:
            raise ValueError("Invalid setter frame")
    elif pc == CONSUMER:
        if operation.arg_a or operation.arg_b:
            raise ValueError("Consumer unused argument fields")
        if esp - 24 < STACK or esp + 4 > STACK + PAGE:
            raise ValueError("Invalid consumer frame")
    else:
        raise ValueError("Unknown operation entry")


def expected_steps(sequence: Sequence) -> tuple[ExpectedStep, ...]:
    """Mutable integer-byte oracle; events are expected, not hardware traces."""
    if not 1 <= len(sequence.steps) <= MAX_STEPS or not isinstance(sequence.seed, int) or not 0 <= sequence.seed <= U32:
        raise ValueError("Invalid sequence extent/seed")
    validate_fx(sequence)
    memory, results = bytearray(initial_memory(sequence)), []
    for operation in sequence.steps:
        _validate_operation(operation)
        cpu, s = list(operation.cpu), operation.cpu[4]
        frame = (SENTINEL, operation.arg_a, operation.arg_b) if cpu[9] == SETTER else (SENTINEL,)
        offset = memory_offset(s, 4 * len(frame))
        memory[offset:offset + 4 * len(frame)] = struct.pack("<" + "I" * len(frame), *frame)
        before, events = bytes(memory), []

        def read(address, width=4):
            offset = memory_offset(address, width)
            value = int.from_bytes(memory[offset:offset + width], "little")
            events.append((address, value, width, 0))
            return value

        def write(address, value, width=4):
            offset = memory_offset(address, width)
            value &= (1 << (width * 8)) - 1
            memory[offset:offset + width] = value.to_bytes(width, "little")
            events.append((address, value, width, 1))

        if cpu[9] == SETTER:
            arg_a = read(s + 4)
            write(GLOBAL + 0x1E8, cpu[2])
            write(GLOBAL + 0x1EC, arg_a)
            arg_b = read(s + 8)
            write(GLOBAL + 0x1F0, arg_b)
            quotient = truncating_half(arg_b)
            sign = U32 if signed(arg_b) < 0 else 0
            write(GLOBAL + 0x1E4, cpu[1])
            write(GLOBAL + 0x1F4, quotient)
            adjusted = (arg_b - sign) & U32
            flags = ((adjusted & 1) | (int((quotient & 255).bit_count() % 2 == 0) << 2) |
                     (int(quotient == 0) << 6) | ((quotient >> 31) << 7))
            cpu[0], cpu[2], cpu[4] = quotient, sign, s + 12
            flag_mask = SETTER_FLAGS
        else:
            for address, value in ((s-12,cpu[3]),(s-16,cpu[5]),(s-20,cpu[6]),(s-24,cpu[7])):
                write(address, value)
            source = read(GLOBAL + 0x1E4)
            write(s - 8, cpu[2])
            if cpu[1] == 0:
                destination, destination_stride = source, read(GLOBAL + 0x1F4)
                write(s - 8, destination_stride)
            else:
                destination, destination_stride = cpu[1], cpu[2]
            rows = signed(read(GLOBAL + 0x1EC)) >> 1
            columns = signed(read(GLOBAL + 0x1E8)) >> 1
            if rows > MAX_ROWS or rows > 0 and columns > MAX_COLUMNS:
                raise ValueError("Consumer work budget exceeded")
            cpu[0] = rows & U32
            if rows > 0:
                write(s - 4, rows)
                source_row, destination_row = source, destination
                for _ in range(rows):
                    if columns > 0:
                        for column in range(columns):
                            source_word = (source_row + 4 * column) & U32
                            destination_word = (destination_row + 2 * column) & U32
                            buffer_span(source_word)
                            buffer_span(destination_word)
                            value = read(source_word, 2)
                            cpu[2] = (cpu[2] & 0xFFFF0000) | value
                            write(destination_word, value, 2)
                    destination_stride = read(s - 8)
                    source_stride = read(GLOBAL + 0x1F4)
                    destination_row = (destination_row + 2 * destination_stride) & U32
                    remaining = (read(s - 4) - 1) & U32
                    source_row = (source_row + 2 * source_stride) & U32
                    write(s - 4, remaining)
                    cpu[0], cpu[1] = remaining, source_stride
            for address, register in ((s-24,7),(s-20,6),(s-16,5),(s-12,3)):
                cpu[register] = read(address)
            left, right, result = (s - 8) & U32, 8, s & U32
            flags = (int(left + right > U32) |
                     (int((result & 255).bit_count() % 2 == 0) << 2) |
                     (int(bool((left ^ right ^ result) & 0x10)) << 4) |
                     (int(result == 0) << 6) | ((result >> 31) << 7) |
                     (int(bool((~(left ^ right) & (left ^ result)) & 0x80000000)) << 11))
            cpu[4] = s + 4
            flag_mask = CONSUMER_FLAGS
        cpu[8] = 0x202 | (operation.cpu[8] & 0x400) | flags
        cpu[9] = read(s)
        if cpu[9] != SENTINEL or len(events) > MAX_EVENTS:
            raise ValueError("Invalid return/trace extent")
        results.append(ExpectedStep(operation.cpu, tuple(cpu), before, bytes(memory), tuple(events), flag_mask))
    return tuple(results)


def validate_sequence(sequence: Sequence) -> None:
    expected_steps(sequence)


def pack_sequences(sequences: list[Sequence] | tuple[Sequence, ...]) -> bytes:
    if not 1 <= len(sequences) <= 100000:
        raise ValueError("Invalid request sequence count")
    return HEADER.pack(b"MW34S3RQ", 1, len(sequences), REQUEST_SIZE, 32) + b"".join(s.pack() for s in sequences)


def unpack_sequences(data: bytes) -> tuple[Sequence, ...]:
    if len(data) < HEADER.size:
        raise ValueError("Truncated request header")
    magic, version, count, size, bits = HEADER.unpack_from(data)
    if magic != b"MW34S3RQ" or version != 1 or not 1 <= count <= 100000 or size != REQUEST_SIZE or bits != 32:
        raise ValueError("Invalid request header")
    if len(data) != HEADER.size + count * REQUEST_SIZE:
        raise ValueError("Request length/trailing bytes")
    result = []
    for index in range(count):
        record = data[HEADER.size + index * size:HEADER.size + (index + 1) * size]
        step_count, seed, tags, reserved = PREFIX.unpack_from(record)
        if not 1 <= step_count <= MAX_STEPS or reserved:
            raise ValueError("Invalid sequence step count/reserved")
        if any(record[528 + step_count * STEP_SIZE:]):
            raise ValueError("Nonzero unused step slots")
        steps = []
        for step_index in range(step_count):
            fields = STEP.unpack_from(record, 528 + step_index * STEP_SIZE)
            steps.append(Operation(tuple(fields[:10]), fields[10], fields[11]))
        sequence = Sequence(tuple(steps), seed, tags, record[16:528])
        validate_sequence(sequence)
        result.append(sequence)
    return tuple(result)


def cases() -> list[Sequence]:
    rng, output = random.Random(SEED), []
    setter_offsets = (0,1,2,3,15,16,17,255,1023,2047,4079,4080,4081,4082,4083,4084)
    consumer_offsets = (24,25,26,27,31,32,33,127,255,1023,2047,4089,4090,4091,4092)

    def operation(pc, *, ecx=None, edx=None, a=0, b=0):
        index = len(output)
        regs = [rng.getrandbits(32) for _ in range(8)]
        if ecx is not None:
            regs[1] = ecx & U32
        if edx is not None:
            regs[2] = edx & U32
        offsets = setter_offsets if pc == SETTER else consumer_offsets
        regs[4] = STACK + offsets[(index + rng.randrange(len(offsets))) % len(offsets)]
        flags = 0x202 | sum((rng.randrange(2) << bit) for bit in (0,2,4,6,7,10,11))
        return Operation(tuple(regs + [flags, pc]), a & U32, b & U32)

    def add(steps, category, *, cw=None, top=None, ftw=None, pattern=None):
        seed = rng.getrandbits(32)
        fx = fx_seed(rng.choice(CWS) if cw is None else cw,
                     rng.randrange(8) if top is None else top,
                     rng.randrange(256) if ftw is None else ftw,
                     rng.choice((0,0x22,0x241,0x457F)),
                     rng.randrange(2) if pattern is None else pattern, seed)
        sequence = Sequence(tuple(steps), seed, full_tags(fx), fx, category)
        validate_sequence(sequence)
        output.append(sequence)

    add((operation(CONSUMER,ecx=0xDEADBEEF,edx=0xA5A5F00D),
         operation(SETTER,ecx=BUFFER+2048,edx=7,a=5,b=65),
         operation(CONSUMER,ecx=0,edx=0x12345678)),
        "zero_initialized_then_configured_operation")
    dimensions = (-5,-3,-2,-1,0,1,2,3,4,5,16,17,32,33)
    columns = (-5,-3,-1,0,1,2,3,4,5,16,17,64,65)
    for row_dimension in dimensions:
        for column_dimension in columns:
            if row_dimension >> 1 > MAX_ROWS:
                continue
            for default in (False, True):
                setup = operation(SETTER,ecx=BUFFER+2049,edx=column_dimension,a=row_dimension,b=128)
                copy = operation(CONSUMER,ecx=0 if default else BUFFER+5601,edx=32)
                again = operation(CONSUMER,ecx=0 if default else BUFFER+5601,edx=32)
                add((setup,copy,again), "signed_odd_counts_default_or_explicit")

    for source_stride in (-96,-65,-1,0,1,65,96):
        for destination_stride in (-48,-1,0,1,48):
            for offset in (-4,-2,-1,0,1,2,3,4,8,16):
                setup = operation(SETTER,ecx=BUFFER+3073,edx=17,a=9,b=source_stride)
                copy = operation(CONSUMER,ecx=BUFFER+3073+offset,edx=destination_stride)
                again = operation(CONSUMER,ecx=0,edx=0xA5A5F00D)
                add((setup,copy,again), "sequential_overlap_signed_strides")

    for source_offset, destination_offset in ((0,8190),(8190,0),(8189,4095),(4095,8189),(4094,4096)):
        setup = operation(SETTER,ecx=BUFFER+source_offset,edx=2,a=2,b=0xFFFFFFFF)
        copy = operation(CONSUMER,ecx=BUFFER+destination_offset,edx=0xA5A5F00D)
        add((setup,copy), "buffer_boundaries_unaligned_upper_DX")

    add((operation(SETTER,ecx=BUFFER+3072,edx=8,a=6,b=0),
         operation(CONSUMER,ecx=BUFFER+4096,edx=0x80000000),
         operation(CONSUMER,ecx=BUFFER+4097,edx=0x80000001)),
        "wrapping_stride_with_reached_valid_words")
    add((operation(SETTER,ecx=0xFFFFFFFE,edx=-3,a=6,b=0x80000000),
         operation(CONSUMER,ecx=0xDEADBEEF,edx=0x79999999)),
        "empty_inner_unmapped_wrapping_pointers")

    for cw in CWS:
        for top in range(8):
            for ftw in (0,2,255):
                for pattern in (0,1):
                    setup = operation(SETTER,ecx=BUFFER+2048,edx=7,a=5,b=-65)
                    copy = operation(CONSUMER,ecx=BUFFER+6144,edx=-16)
                    add((setup,copy), "persistent_live_FP_vector_state",cw=cw,top=top,ftw=ftw,pattern=pattern)

    for _ in range(128):
        rows, cols = rng.randrange(1,9), rng.randrange(1,17)
        source = BUFFER+3072+rng.randrange(2)
        stride = rng.randrange(-96,97)
        setup = operation(SETTER,ecx=source,edx=2*cols+rng.randrange(2),a=2*rows+rng.randrange(2),b=stride)
        explicit = operation(CONSUMER,ecx=BUFFER+6144+rng.randrange(2),edx=rng.randrange(-48,49))
        alias = operation(CONSUMER,ecx=source+rng.choice((-4,-2,0,2,4,8)),edx=rng.randrange(-32,33))
        reconfigure = operation(SETTER,ecx=BUFFER+4097,edx=rng.choice((-3,0,1,3,9,17)),
                                a=rng.choice((-3,0,1,3,9)),b=rng.randrange(-65,66))
        default = operation(CONSUMER,ecx=0,edx=rng.getrandbits(32))
        add((setup,explicit,alias,reconfigure,default), "seeded_reconfiguration_connected_sequence")

    # A full maximum-length sequence makes truncation/suffix admission observable.
    steps = [operation(SETTER,ecx=BUFFER+2048,edx=64,a=32,b=128)]
    steps.extend(operation(CONSUMER,ecx=0 if i&1 else BUFFER+5120,edx=32) for i in range(15))
    add(steps, "maximum_steps_and_work_budget")
    return output


def coverage(sequences: list[Sequence] | tuple[Sequence, ...]) -> dict:
    operations = Counter(step.cpu[9] for sequence in sequences for step in sequence.steps)
    return {"sequence_count":len(sequences),"step_count":sum(len(s.steps) for s in sequences),
            "setter_steps":operations[SETTER],"consumer_steps":operations[CONSUMER],
            "categories":dict(Counter(s.category for s in sequences)),
            "control_words":sorted({struct.unpack_from('<H',s.fx)[0] for s in sequences}),
            "TOP_values":sorted({(struct.unpack_from('<H',s.fx,2)[0]>>11)&7 for s in sequences}),
            "physical_FTW_values":sorted({s.fx[4] for s in sequences}),
            "maximum_trace_events":max(len(row.events) for s in sequences for row in expected_steps(s)),
            "maximum_steps":max(len(s.steps) for s in sequences),"seed":SEED,
            "inputs_are_recordings":False,"execution_performed_by_oracle":False}

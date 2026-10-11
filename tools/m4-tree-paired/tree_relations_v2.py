"""Typed cross-branch tree relations from separately proven literal source.

The two allocation branches retain their own real identities and initial
capacity bytes. Only exact source-established pointer fields and two literal
saved-local bytes receive branch-relative relations; no whole-page mask exists.
"""
import collections
import json
import struct
from pathlib import Path

TREE = 0x4b7f70
TREE_PHASE = 77
LOCAL_BYTES = {(0x4b7da6, 0x60b2f9, 1), (0x4b7daf, 0x60b2f8, 1)}


def need(value, label):
    if not value:
        raise ValueError(label)


def same(a, b, label):
    need(a == b, label + ' ' + str((a, b))[:600])


def pointer(value, owners):
    if value == 0:
        return None
    matches = [o['index'] for o in owners if o['guest'] == value]
    need(len(matches) == 1, 'Typed non-null node pointer is one exact current owner base')
    return matches[0]


def local_provenance(source, write):
    read_pc = 0x4b7d98 if write['pc'] == 0x4b7daf else 0x4b7da0
    frames = [f for f in source['FS_frames'] if f['entry'] == 0x4b7d80]
    need(len(frames) == 1, 'One exact source lower tree frame')
    frame = frames[0]
    functions = [f for f in source['function_invocations'] if f['index'] == frame['invocation']]
    need(len(functions) == 1, 'Exact source frame invocation is retained')
    first = functions[0]['source_access_index']
    matches = [(i, r) for i, r in enumerate(source['source_accesses'])
               if r[0] == read_pc and r[3] == 1 and not r[4]]
    need(len(matches) == 1, 'One genuine literal saved-local byte read')
    index, read = matches[0]
    need(first <= index < write['source_access_index'] and read[1] == frame['entry_ESP'] - 41,
         'Exact lower source frame saved-local read before its literal publication')
    need(read[2] == write['value'], 'The literal static byte is its own genuine source read')
    need(not any(r[4] and r[1] <= read[1] < r[1] + r[3]
                 for r in source['source_accesses'][first:index]),
         'Saved-local input has no current-invocation overlapping source store before the read')
    return dict(read_pc=read_pc, address=read[1], value=read[2], read_index=index,
                store_pc=write['pc'], store_index=write['source_access_index'], invocation=frame['invocation'])


def compare(original, native, native_capture, stem, contract):
    counts = collections.Counter()
    original_owners = original['owners']
    native_owners = native['owners']
    need(len(original_owners) == len(native_owners) == 7, 'Seven actual tree occurrences in both branches')
    need(original['candidate_AFTER_seed'] is False and native['candidate_AFTER_seed'] is False,
         'Both literal tree models derive their own effects')
    actual = [row for row in struct.iter_unpack('<32Q', native_capture.data(stem + 'mfc-allocation-witnesses.bin'))
              if row[2] == TREE]
    need(len(actual) == 7, 'Seven actual full125 native tree witnesses')
    for index, (a, b, witness) in enumerate(zip(original_owners, native_owners, actual)):
        same((a['index'], a['CALL_pc'], a['per_site_invocation_ordinal'], a['requested']),
             (b['index'], b['CALL_pc'], b['per_site_invocation_ordinal'], b['requested']),
             'Literal owner role, repeated CALL occurrence and requested extent')
        need(a['index'] == b['index'] == index and a['requested'] == b['requested'] == 24,
             'Source-defined finite seven-role owner order')
        same((witness[4], witness[7], witness[16], witness[17], witness[18], witness[19]),
             (b['CALL_pc'], b['requested'], b['guest'], b['native'], b['generation'], b['capacity']),
             'Source role is the actual native current generation and capacity')
        need(witness[21] == witness[23] == 1, 'Actual single positive source publication')
        a_initial = bytes.fromhex(a['initial_hex'])
        b_initial = bytes.fromhex(b['initial_hex'])
        a_final = bytes.fromhex(a['source_final_hex'])
        b_final = bytes.fromhex(b['source_final_hex'])
        need(len(a_initial) == len(a_final) == a['capacity'] == 32,
             'Whole genuine original capacity is modeled')
        need(len(b_initial) == len(b_final) == b['capacity'] == 32,
             'Whole genuine native capacity is modeled')
        same(native_capture.data(stem + f'locale-allocation-{b["generation"]}-initial.bin'),
             b_initial, 'Actual current native initial capacity backing')
        expected = b_final + bytes(4096 - len(b_final))
        same(native_capture.data(stem + f'locale-allocation-{b["generation"]}-expected.bin'),
             expected, 'Whole native expected mapping derives from literal writes')
        same(native_capture.data(stem + f'locale-allocation-{b["generation"]}-owned-page.bin'),
             expected, 'Whole actual native mapping is the source-owned result')
        a_written = set()
        b_written = set()
        for owner, result in ((a, a_written), (b, b_written)):
            model = original if owner is a else native
            for row in model['owned_accesses']:
                if row['owner_index'] == index and row['write']:
                    result.update(range(row['offset'], row['offset'] + row['bytes']))
        same(a_written, b_written, 'Exact source-established byte domain per owner occurrence')
        for offset in range(0, 24, 4):
            domain = set(range(offset, offset + 4))
            if domain <= a_written:
                av = int.from_bytes(a_final[offset:offset + 4], 'little')
                bv = int.from_bytes(b_final[offset:offset + 4], 'little')
                if offset in (0, 4, 8):
                    same(pointer(av, original_owners), pointer(bv, native_owners),
                         'Every initialized node link has the same exact nullable owner role')
                else:
                    same(av, bv, 'Every initialized key/borrowed-static-pointer/color scalar is exact')
                counts['tree_initialized_DWORD_relations'] += 1
            else:
                need(not domain & a_written, 'No partially initialized DWORD is assigned a blanket relation')
        for offset in set(range(32)) - a_written:
            need(a_final[offset] == a_initial[offset] and b_final[offset] == b_initial[offset],
                 'Untouched own-branch byte retains its genuine initial backing')
            counts['tree_untouched_capacity_byte_relations'] += 1
        counts['tree_whole_branch_owner_backing_pairs'] += 1

    need(len(original['owned_accesses']) == len(native['owned_accesses']) == 172,
         'Complete actual literal tree owner causal order')
    causal = contract['owned_causal_order']
    need(len(causal) == 172, 'Frozen original-corroborated complete causal contract')
    for a, b, spec in zip(original['owned_accesses'], native['owned_accesses'], causal):
        keys = ('pc', 'write', 'bytes', 'owner_CALL_pc', 'owner_invocation_ordinal', 'owner_index', 'offset')
        same(tuple(a[k] for k in keys), tuple(b[k] for k in keys), 'Every exact source-owned access role/order')
        same((a['pc'], a['owner_index'], a['offset'], a['bytes'], bool(a['write'])),
             (spec['pc'], spec['owner_role_index'], spec['offset'], spec['bytes'], bool(spec['write'])),
             'Every actual operand is the exact frozen PC/role/width/direction occurrence')
        if a['offset'] in (0, 4, 8):
            av, bv = pointer(a['value'], original_owners), pointer(b['value'], native_owners)
            same(av, bv, 'Every nullable link operand has the same typed current owner role')
            same(av, spec['value_owner_role_index'], 'Pointer read/write is its exact source-corroborated role')
        else:
            need(a['offset'] in (12, 16, 20) and spec['value_owner_role_index'] is None,
                 'Key/borrowed static/color operands have their declared scalar field type')
            same(a['value'], b['value'], 'Source-owned scalar or borrowed static operand is exact')
        counts['tree_paired_owned_accesses'] += 1

    a_writes = original['static_field_writes']
    b_writes = native['static_field_writes']
    same([(r['pc'], r['address'], r['width']) for r in a_writes],
         [(r['pc'], r['address'], r['width']) for r in b_writes],
         'Complete ordered literal static field writes')
    fields = {}
    for a, b in zip(a_writes, b_writes):
        spec = (a['pc'], a['address'], a['width'])
        if spec in LOCAL_BYTES:
            need(a['width'] == 1 and 0 <= a['value'] <= 255 and 0 <= b['value'] <= 255,
                 'Only the two physical saved-local byte writes receive own-branch values')
            counts['tree_saved_local_byte_relations'] += 1
            local_provenance(original, a)
            local_provenance(native, b)
            counts['tree_literal_saved_local_read_to_store_joins'] += 2
        elif spec in {(0x4ba315, 0x60b314, 4), (0x4ba347, 0x60b2fc, 4)}:
            role = 0 if a['pc'] == 0x4ba315 else 1
            same(pointer(a['value'], original_owners), role, 'Original typed primary owner publication')
            same(pointer(b['value'], native_owners), role, 'Native typed primary owner publication')
        else:
            same(a['value'], b['value'], 'Every remaining literal static scalar is exact')
        av = a['value'].to_bytes(a['width'], 'little')
        bv = b['value'].to_bytes(b['width'], 'little')
        for offset in range(a['width']):
            fields[a['address'] + offset] = (av[offset], bv[offset], a['pc'])
        counts['tree_paired_static_source_writes'] += 1
    need({(r['pc'], r['address'], r['width']) for r in a_writes} >= LOCAL_BYTES,
         'Both exact source saved-local byte declarations are present')
    return fields, dict(counts)


def carry(fields, phase, side, page, original, native, declared, counts):
    if phase < TREE_PHASE or (phase == TREE_PHASE and side == 'before'):
        return
    for address, (a, b, pc) in fields.items():
        if address & ~4095 != page:
            continue
        offset = address & 4095
        need(original[offset] == a and native[offset] == b,
             f'Exact source-established tree static byte carry {phase}/{side}/{address:08x}/{pc:08x}')
        declared.add(offset)
        counts['tree_static_byte_endpoint_carries'] += 1

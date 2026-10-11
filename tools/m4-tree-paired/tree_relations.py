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


def identity(value, owners):
    matches = [(o['index'], value - o['guest']) for o in owners
               if o['guest'] <= value < o['guest'] + o['requested']]
    need(len(matches) <= 1, 'Unambiguous actual live tree owner')
    return ('owner', *matches[0]) if matches else ('scalar', value)


def compare(original, native, native_capture, stem):
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
                same(identity(av, original_owners), identity(bv, native_owners),
                     'Every complete initialized field has the same null/scalar/borrowed/owner role')
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
    for a, b in zip(original['owned_accesses'], native['owned_accesses']):
        keys = ('pc', 'write', 'bytes', 'owner_CALL_pc', 'owner_invocation_ordinal', 'owner_index', 'offset')
        same(tuple(a[k] for k in keys), tuple(b[k] for k in keys), 'Every exact source-owned access role/order')
        same(identity(a['value'], original_owners), identity(b['value'], native_owners),
             'Every source-owned operand value has the same exact owner-relative meaning')
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
        else:
            same(identity(a['value'], original_owners), identity(b['value'], native_owners),
                 'Literal static scalar or live owner-relative field relation')
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

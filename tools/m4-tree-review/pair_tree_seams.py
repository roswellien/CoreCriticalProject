"""Finite cross-branch tree scratch/API and whole FS-record relations.

Inputs are sealed source exports. The separate producing gates authenticate
actual CPU/API/record bytes. No archive is reopened and no postRET observation
or original/native volatile register equality is invented here.
"""
import struct


def need(value, message):
    if not value:
        raise ValueError(message)


def same(a, b, message):
    need(a == b, message + ' ' + repr((a, b))[:400])


def cs(raw, thread):
    words = list(struct.unpack('<6I', bytes.fromhex(raw)))
    depth = words[2]
    need(words[3] == (thread if depth else 0), 'CS24 owner is the own authenticated current thread at its literal depth')
    words[3] = int(bool(depth))
    return words


def compare(original, native, relations, counts):
    acalls, bcalls = original['Lockit_calls'], native['Lockit_calls']
    need(len(acalls) == len(bcalls) == len(relations) == 26, 'All26 actual literal tree scratch/API roles')
    joins = original['original_boundary_joins']
    need(len(joins) == 78, 'Three original observations per true literal CALL')
    athreads = {struct.unpack_from('<I', bytes.fromhex(p['returned']['source_CS24_hex']), 12)[0]
                for p in acalls if p['role'].endswith('ctor')}
    bthreads = {r['OwningThread'] for r in relations if r['OwningThread']}
    need(len(athreads) == len(bthreads) == 1 and 0 not in athreads,
         'One genuine own current thread in each branch')
    athread, bthread = next(iter(athreads)), next(iter(bthreads))
    held = []
    observations = []
    for ordinal, (a, b, api) in enumerate(zip(acalls, bcalls, relations)):
        keys = ('CALL_pc', 'role', 'invocation', 'ECX', 'target_entry_ESP', 'scratch_offset', 'target')
        same(tuple(a[k] for k in keys), tuple(b[k] for k in keys), 'Exact repeated CALL/scratch/current function invocation identity')
        same(tuple(a['LEA'][k] for k in ('PC', 'value', 'ESP', 'invocation')),
             tuple(b['LEA'][k] for k in ('PC', 'value', 'ESP', 'invocation')),
             'Exact originating source LEA at this invocation')
        ctor = a['role'].endswith('ctor')
        entry, atapi, returned = joins[3 * ordinal:3 * ordinal + 3]
        same([p['kind'] for p in (entry, atapi, returned)], [0, 1, 2] if ctor else [3, 4, 5],
             'Actual original constructor/destructor observer ordering')
        frame = a['target_entry_ESP'] - (16 if ctor else 8)
        same((entry['CPU'][4], entry['CPU'][9]), (a['target_entry_ESP'], a['target']), 'Genuine original target entry frame')
        same((atapi['CPU'][4], returned['CPU'][4], returned['CPU'][9]),
             (frame, frame + 8, 0x7810a311 if ctor else 0x7810a364),
             'Actual original API frame and bounded pre-epilogue APIreturn PC')
        same((api['frame'], api['source_PC'], api['return_pc'], api['guest_CS']),
             (frame, 0x7810a30b if ctor else 0x7810a35e, returned['CPU'][9], 0x78145640),
             'Native actual stdcall/source-return relation for the same literal scratch role')
        same(cs(atapi['source_CS24_hex'], athread), cs(b['entered']['source_CS24_hex'], bthread),
             'Whole typed24B input semantics, with own current-thread identity')
        same(cs(returned['source_CS24_hex'], athread), cs(api['derived_CS24_hex'], bthread),
             'Whole typed24B output semantics, with own current-thread identity')
        same(api['derived_CS24_hex'], b['returned']['source_CS24_hex'], 'Native source CALL return retains complete actual API-derived CS24')
        before_depth = struct.unpack_from('<I', bytes.fromhex(atapi['source_CS24_hex']), 8)[0]
        need(api['depth'] == before_depth + (1 if ctor else -1), 'Each exact API effects one recursive depth transition')
        if ctor:
            held.append((a['CALL_pc'], a['invocation'], a['ECX']))
        else:
            need(held and held[-1] == (a['matching_constructor_CALL_pc'], a['matching_constructor_invocation'], a['ECX']),
                 'Exact original live constructor/same scratch LIFO pairing')
            same((a['matching_constructor_CALL_pc'], a['matching_constructor_invocation']),
                 (b['matching_constructor_CALL_pc'], b['matching_constructor_invocation']),
                 'Exact native matched constructor provenance, including shared dtor branch')
            held.pop()
        counts['tree_scratch_role_pairs'] += 1
        counts['tree_typed_API_semantic_pairs'] += 1
        observations.append(dict(ordinal=ordinal, CALL_pc=a['CALL_pc'], role=a['role'], invocation=a['invocation'],
                                 scratch=a['ECX'], original_APIentry_PC=atapi['CPU'][9], API_frame=frame,
                                 native_API_index=api['API_index'], depth=api['depth'], original_thread=athread,
                                 native_thread=bthread, original_APIreturn_PC=returned['CPU'][9]))
    need(not held and max(r['depth'] for r in relations) == 2, 'All13 scratch pairs balanced; actual recursive maximum2')
    aframes, bframes = original['FS_frames'], native['FS_frames']
    need(len(aframes) == len(bframes) == 7, 'Every repeated normal tree FS invocation')
    for a, b in zip(aframes, bframes):
        keys = ('index', 'entry', 'invocation', 'handler', 'read_PC', 'entry_ESP', 'depth', 'closed', 'record', 'install_PC', 'restore_PC')
        same(tuple(a[k] for k in keys), tuple(b[k] for k in keys), 'Exact source invocation/handler/record/normal FS lifetime')
        need(a['closed'] and b['closed'] and a['record'] == a['entry_ESP'] - 12, 'Complete installed frame12 and normal restoration')
        if a['depth']:
            same(a['previous_head'], b['previous_head'], 'Nested FS predecessor is the same exact active guest record')
            need(a['previous_head'] == aframes[0]['record'], 'Every normal nested invocation points to the live outer frame')
        for key in ('installed_hex', 'restored_hex'):
            aw, bw = struct.unpack('<3I', bytes.fromhex(a[key])), struct.unpack('<3I', bytes.fromhex(b[key]))
            same(aw[0], a['previous_head'], 'Complete original record retains its own literal saved predecessor')
            same(bw[0], b['previous_head'], 'Complete native record retains its own literal saved predecessor')
            same(aw[1:], bw[1:], 'Exact complete source handler/scopeDWORDs in each12B record')
            counts['tree_complete12B_FS_pairs'] += 1
        astore, bstore = a['restore_scope_source_store'], b['restore_scope_source_store']
        same(tuple(astore[k] for k in ('pc', 'address', 'value', 'bytes')),
             tuple(bstore[k] for k in ('pc', 'address', 'value', 'bytes')), 'Exact final source scope store provenance')
    return observations

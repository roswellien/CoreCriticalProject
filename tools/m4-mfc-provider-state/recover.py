"""Narrow original-byte MFC state prerequisite recovery; never executes code.

Uses the frozen full disassembly only as a decoding record. Selected roots are
checked against admitted PE bytes and prior source receipts; calls are explicit
frontiers, never implicit semantic implementation credit.
"""
import copy
import hashlib
import json
import ntpath
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage

MFC_SHA = '5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'
CRT_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
GAME_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'


def need(ok, why):
    if not ok: raise ValueError(why)


def digest(data): return hashlib.sha256(data).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def pointer(doc, path):
    for item in path[1:].split('/'):
        item = item.replace('~1', '/').replace('~0', '~')
        doc = doc[int(item)] if isinstance(doc, list) else doc[item]
    return doc


def raw(pe, va, length):
    offset, _ = pe.rva_range(va - pe.image_base, length)
    return pe.data[offset:offset+length]


def decoded_rows(text, pe):
    rows = {}
    for line in text.splitlines():
        match = re.fullmatch(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(\S+)(?:\s+(.*))?', line)
        if not match: continue
        va = int(match[1], 16)
        code = bytes.fromhex(match[2])
        # Only selected reachable instructions will be physically checked below.
        rows[va] = dict(pc=va, size=len(code), mnemonic=match[3], operands=match[4] or '',
                        bytes=code.hex(), sha256=digest(code))
    return rows


def target(operand):
    match = re.fullmatch(r'0x([0-9a-f]+)(?: <[^>]+>)?', operand)
    return int(match[1], 16) if match else None


def cfg(entry, rows, pe):
    pending, seen, edges, calls, exits = [entry], set(), {}, [], []
    while pending:
        pc = pending.pop()
        if pc in seen: continue
        need(pc in rows, f'Missing exact decoded boundary {pc:08X}')
        need(len(seen) < 8192, 'Bounded local CFG limit')
        seen.add(pc)
        row = rows[pc]
        need(raw(pe, pc, row['size']).hex() == row['bytes'], 'Actual selected source bytes')
        op, operand, nxt = row['mnemonic'], row['operands'], pc+row['size']
        if op.startswith('j') or op.startswith('loop'):
            dest = target(operand)
            if dest is None:
                successors = []
                exits.append(dict(pc=pc, kind='unresolved indirect branch', operands=operand))
            else: successors = [dest] if op == 'jmp' else [dest, nxt]
        elif op in ('ret', 'retf', 'iret', 'int3', 'ud2'):
            successors = []
            exits.append(dict(pc=pc, kind=op, operands=operand))
        else:
            successors = [nxt]
            if op == 'call': calls.append(dict(pc=pc, target_va=target(operand), operands=operand))
        edges[str(pc)] = successors
        pending.extend(successors)
    ordered = [rows[pc] for pc in sorted(seen)]
    return dict(entry_va=entry, instruction_count=len(ordered), instructions=ordered, edges=edges,
                calls=sorted(calls,key=lambda c:c['pc']), exits=sorted(exits,key=lambda c:c['pc']),
                concatenated_instruction_bytes_sha256=digest(b''.join(bytes.fromhex(r['bytes']) for r in ordered)),
                closure_limit='Local reachable instruction CFG only. Calls not inlined; indirect routes, exceptional dispatch, resources, semantic ownership and actual provider selection remain gates.')


def validate(doc, images, old, source_rows):
    need(doc['images']['game']['sha256'] == GAME_SHA and
         doc['images']['mfc42_staged']['sha256'] == MFC_SHA and
         doc['images']['msvcrt_staged']['sha256'] == CRT_SHA, 'Exact admitted images')
    need(doc['native_execution_credit'] is False and doc['source_implementation_credit'] is False and
         doc['actual_loaded_mfc_provider'] is None, 'Static-only and actual-provider unknown scope')
    for body in doc['bodies']:
        pe = images[body['image']]
        for instruction in body['graph']['instructions']:
            pc = instruction['pc']
            need(instruction == source_rows[body['image']][pc] and
                 raw(pe,pc,instruction['size']).hex() == instruction['bytes'], 'Selected source identity')
        expected = cfg(body['graph']['entry_va'],source_rows[body['image']],pe)
        need(body['graph'] == expected, 'Deterministic complete local CFG')
        if body.get('prior_source'):
            ref=body['prior_source']
            value=pointer(old[ref['receipt']],ref['pointer'])
            need(digest(canonical(value)) == ref['value_sha256'], 'Exact frozen root JSON association')
            need([(i['pc'],i['bytes']) for i in value['instructions']] ==
                 [(i['pc'],i['bytes']) for i in body['graph']['instructions']], 'Recovered root instruction association')
    order=doc['gate_order']
    need(len(order)==len(set(order))==len(doc['gates']), 'Unique complete gate inventory')
    indices={gate:i for i,gate in enumerate(order)}
    for gate in doc['gates']:
        need(gate['implemented'] is False and gate['native_credit'] is False, 'Prerequisite gates not implemented')
        need(all(indices[d]<indices[gate['id']] for d in gate['depends']), 'Explicit prerequisite DAG ordering')
    facts={f['id']:f for f in doc['source_facts']}
    for fact in facts.values():
        for ref in fact['instructions']:
            need(source_rows[ref['image']][ref['pc']]['bytes']==ref['bytes'], 'Literal fact/source association')
    need(facts['app_receiver_publication']['instructions'][-1]['pc']==0x5f40ae75 and
         facts['app_receiver_publication']['receiver_va']==0x608c88 and
         facts['app_receiver_publication']['module_state_offset']==4, 'Conditional constructor receiver link')
    need(facts['thread_access']['factory_call_pc']==0x5f401067 and
         facts['thread_access']['factory_argument_offset']==12, 'Actual factory argument before internal CALL')
    need(doc['guest_seh_contract']['FS0_effect']=='Guest chain registration and restore; host FS/TEB never substituted' and
         doc['guest_seh_contract']['prolog_bytes']=='6aff5064a100000000508b44240c64892500000000896c240c8d6c240c50c3',
         'Exact guest exception-chain prolog')


def main():
    out=ROOT/'reports/m4-mfc-provider-state/recovery-r1'
    need(not out.exists(),'Fresh owned output required')
    files={}
    def bind(path, expected=None):
        path=Path(path).absolute()
        data=path.read_bytes(); actual=digest(data)
        key=ntpath.normcase(ntpath.normpath(str(path)))
        need(expected is None or expected==actual,'Expected source/receipt hash')
        need(key not in files or files[key]['sha256']==actual,'Conflicting lexical identity')
        files[key]=dict(path=str(path),size_bytes=len(data),sha256=actual)
        return files[key]
    image_paths=dict(game=ROOT/'MW3/Mech3.exe',mfc42_staged=ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL',
                     msvcrt_staged=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')
    identities={name:bind(path,{'game':GAME_SHA,'mfc42_staged':MFC_SHA,'msvcrt_staged':CRT_SHA}[name]) for name,path in image_paths.items()}
    images={name:PEImage(path.read_bytes()) for name,path in image_paths.items()}
    bind(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    bind(Path(__file__))
    inv_path=ROOT/'reports/m4-application-workahead/preparation-r4/inventory.json'
    bind(inv_path,'e7a8902f7e51e13244205e7aa137470f53f5544322d9094d3f0f937c0e892dc1')
    inv=json.loads(inv_path.read_text())
    prior_paths={'mfc':ROOT/'reports/m4-startup/services/mfc-callback-recovery.json',
                 'app':ROOT/'reports/m4-startup/services/application-chain-report.json'}
    prior_hashes={'mfc':'fd8b30254b4006819db867b41417745a83722943ebf60e3ba45ff2f5089898fe',
                  'app':'89496fb8a211b17b1e29a0ce2b90c1d713ef1705ab40e446a7139ef27899cbdb'}
    prior_ids={key:bind(path,prior_hashes[key]) for key,path in prior_paths.items()}
    old={key:json.loads(path.read_text()) for key,path in prior_paths.items()}
    dis_paths={'mfc42_staged':ROOT/'reports/m4-startup/services/staged-mfc42-private-disassembly.txt',
               'msvcrt_staged':ROOT/'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout'}
    dis_ids={key:bind(path,'117567a73a992f9e333f8b03fd8c850fc90e057e7727dfb9de690552db28f3a9' if key=='mfc42_staged' else None)
             for key,path in dis_paths.items()}
    rows={key:decoded_rows(path.read_text(),images[key]) for key,path in dis_paths.items()}
    roots={0x5f401083:('mfc','/provider_cfgs/1'),0x5f4021df:('app','/provider_constructor_cfgs/2'),
           0x5f40aefa:('app','/provider_constructor_cfgs/1'),0x5f40ae1b:('app','/provider_constructor_cfgs/0'),
           0x5f40afb7:('mfc','/provider_cfgs/2'),0x5f40b35d:('mfc','/provider_cfgs/0')}
    helpers=[0x5f401000,0x5f40107d,0x5f4010ab,0x5f40a21d,0x5f40a25e,0x5f405466,
             0x5f4053fe,0x5f405432,0x5f40544f,0x5f40b293,0x5f40b2df,0x5f4016f0,0x5f401761,0x5f405631]
    bodies=[]
    for entry in sorted(set(roots)|set(helpers)):
        body=dict(image='mfc42_staged',graph=cfg(entry,rows['mfc42_staged'],images['mfc42_staged']),
                  recovery='Rechecked frozen root' if entry in roots else 'Narrow newly selected local helper CFG')
        if entry in roots:
            receipt,path=roots[entry]
            body['prior_source']=dict(receipt=receipt,pointer=path,value_sha256=digest(canonical(pointer(old[receipt],path))))
        bodies.append(body)
    export=next(e for e in images['msvcrt_staged'].exports() if '_EH_prolog' in e['names'])
    need(images['msvcrt_staged'].image_base+export['rva']==0x78001496,'Staged actual named _EH_prolog entry')
    bodies.append(dict(image='msvcrt_staged',graph=cfg(0x78001496,rows['msvcrt_staged'],images['msvcrt_staged']),
                       recovery='Narrow actual named imported prolog CFG',export=export))
    imports={images['mfc42_staged'].image_base+s['iat_rva']:dict(library=lib['library'],**s)
             for lib in images['mfc42_staged'].imports() for s in lib['symbols']}
    selected_entries={b['graph']['entry_va'] for b in bodies if b['image']=='mfc42_staged'}
    edges=[]
    for body in bodies:
        if body['image']!='mfc42_staged':continue
        for call in body['graph']['calls']+body['graph']['exits']:
            if 'target_va' not in call and call['kind']!='unresolved indirect branch':continue
            operand=call['operands']; match=re.fullmatch(r'dword ptr \[0x([0-9a-f]+)\]',operand)
            slot=int(match[1],16) if match else None
            dest=call.get('target_va')
            edge=dict(owner=body['graph']['entry_va'],pc=call['pc'],operands=operand,
                      kind='CALL' if 'target_va' in call else 'tail branch',target_va=dest,
                      disposition='selected helper local CFG only' if dest in selected_entries else
                                  'direct helper missing dependency closure' if dest is not None else
                                  'exact IAT import service still required' if slot in imports else
                                  'unresolved indirect receiver/function pointer')
            if slot in imports:edge.update(iat_va=slot,raw_iat_word=struct.unpack('<I',raw(images['mfc42_staged'],slot,4))[0],import_identity=imports[slot])
            edges.append(edge)
    def refs(pcs,image='mfc42_staged'):
        return [dict(image=image,pc=pc,bytes=rows[image][pc]['bytes']) for pc in pcs]
    facts=[
        dict(id='thread_access',instructions=refs([0x5f401002,0x5f401010,0x5f401012,0x5f40101c,0x5f401021,0x5f401024,0x5f401067,0x5f401076]),
             key_holder='ECX at entry; DWORD[key_holder] selects slot; 0 invokes actual key allocation',
             manager_global=0x5f4cb000,manager_TLS_index_offset=0,TLS_object_bound_offset=8,TLS_array_pointer_offset=12,
             factory_call_pc=0x5f401067,factory_argument_offset=12,
             lifetime='Actual factory result is retained as slot object and returned; owning destruction/TLS cleanup remains unrecovered'),
        dict(id='module_access',instructions=refs([0x5f401083,0x5f401088,0x5f401092,0x5f40109a,0x5f40109f,0x5f4010a4]),
             thread_factory=0x5f4053fe,thread_key_holder=0x5f4cb03c,current_module_pointer_offset=4,
             fallback_factory=0x5f40b293,fallback_holder=0x5f4cb040,
             lifetime='Source selects current per-thread module pointer or lazily created shared fallback; file-zero globals prove neither initialization nor allocation'),
        dict(id='factories',instructions=refs([0x5f405409,0x5f40540e,0x5f405421,0x5f40b29f,0x5f40b2a4,0x5f40b2c5,0x5f40563c,0x5f405641,0x5f405654,0x5f405439]),
             allocation_sizes=[0x118,0x1090,0x84],allocation_service='KERNEL32!LocalAlloc through5432; source flag0x40',
             constructors=[0x5f40544f,0x5f40b2df,0x5f405665],
             limitation='Concrete sizes and source constructors only; object layout/teardown/handle ownership and failure paths not complete'),
        dict(id='shared_lazy_access',instructions=refs([0x5f4010c3,0x5f4010c8,0x5f4010db,0x5f4010dd,0x5f4010e6,0x5f4010eb,0x5f4010ee,0x5f4010f6]),
             receiver='ECX exact holder address',factory='Actual cdecl stack argument[EBP+8]',
             lock_index=16,normal_ret_bytes=4,
             limitation='Fast initialized-holder branch still installs/removes guest SEH; double-check lock slow branch not replaceable with unconditional zero or host pointer'),
        dict(id='app_receiver_publication',instructions=refs([0x5f4021fc,0x5f402206,0x5f40ae4a,0x5f40ae4d,0x5f40ae52,0x5f40ae58,0x5f40ae5d,0x5f40ae75]),
             receiver_va=0x608c88,module_state_offset=4,receiver_saved_module_offset=0x1c,
             thread_factory=0x5f405631,per_module_thread_key_offset=0x108c,
             limitation='Static conditional link from admitted game constructor; actual module/thread selection and successful complete object construction required'),
        dict(id='application_callback_gate',instructions=refs([0x5f40b362,0x5f40b36b]),
             module_accessor=0x5f401083,application_slot_offset=4,
             limitation='No live receiver, construction-completion, vtable capability, nonvolatile/FP/exception closure or callback execution credit'),
        dict(id='guest_seh',instructions=refs([0x78001499,0x780014a4,0x780014ab,0x780014af,0x780014b4],'msvcrt_staged')),
    ]
    gates=[
        dict(id='provider-selection',depends=[],roots=[],requirement='Observe/admit actual selected MFC provider, exact image/relocation/raw imports. Staged source contract cannot select Windows provider.'),
        dict(id='guest-SEH',depends=['provider-selection'],roots=[0x5f40107d,0x78001496],requirement='Guest FS base/chain mapped, owned registration frames, source prolog and restoration, actual exception/failure boundary and stack partial-fault order.'),
        dict(id='platform-resources',depends=['provider-selection'],roots=[0x5f40a21d,0x5f4016f0,0x5f401761,0x5f405432],requirement='Typed guest TLS indices/values, LocalAlloc/GlobalAlloc handles+buffers, critical sections and thread identities; host values never untyped guest pointers.'),
        dict(id='thread-slots',depends=['guest-SEH','platform-resources'],roots=[0x5f401000,0x5f40a21d,0x5f40a25e,0x5f405466],requirement='Prove key allocation, manager construction, actual TLS-array growth/publish, callbacks and slot lifetimes. Recover all called/cold/failure dependencies before native admission.'),
        dict(id='module-factories',depends=['guest-SEH','platform-resources','thread-slots'],roots=[0x5f4053fe,0x5f40b293,0x5f40b2df,0x5f4010ab],requirement='Complete0x118 thread-module and0x1090 module factory layouts; lazy holder lock16 and exact allocation/destruction/SEH paths.'),
        dict(id='module-context',depends=['thread-slots','module-factories'],roots=[0x5f401083],requirement='Admit correct thread-local module pointer or source-backed fallback; preserve nesting and restore semantics, no preseeded app pointer.'),
        dict(id='app-object-lifetime',depends=['guest-SEH','module-context'],roots=[0x5f4021df,0x5f40aefa,0x5f40ae1b,0x5f405631],requirement='Complete base/derived construction, matching608C88 receiver, module+4 and per-module-thread+4 publications, actual vtable identity, paired teardown and no stale receiver.'),
        dict(id='application-native-callback',depends=['app-object-lifetime'],roots=[0x5f40afb7,0x5f40b35d],requirement='Recover remaining helpers/virtual receiver guards and admit exact game callbacks+ABI with original BEFORE source model. Window/menu/backends remain subsequent gates.'),
    ]
    for gate in gates:gate.update(implemented=False,native_credit=False)
    globals=[]
    for va in [0x5f4cb000,0x5f4cb008,0x5f4cb03c,0x5f4cb040,0x5f4cb048,0x5f4cb1e0,0x5f4cb1e8,0x5f4cca00,0x5f4cca48]:
        code=raw(images['mfc42_staged'],va,4)
        globals.append(dict(va=va,raw_file_bytes=code.hex(),raw_file_DWORD=struct.unpack('<I',code)[0],
                            initialized_runtime_value=None,limitation='File backing identity only; no loader/provider initialization or lifetime proof'))
    doc=dict(schema_version=1,evidence_kind='Independent narrow exact-source prerequisite recovery; no code execution',
             images=identities,prior_receipts=prior_ids,source_disassemblies=dis_ids,
             native_execution_credit=False,source_implementation_credit=False,actual_loaded_mfc_provider=None,
             bodies=bodies,source_edges=edges,source_facts=facts,raw_provider_globals=globals,
             gate_order=[g['id'] for g in gates],gates=gates,
             guest_seh_contract=dict(entry_ESP='S with actual caller return word at[S]',entry_EAX='Exact source EH metadata',
                 entry_EBP='Prior guest EBP',prolog_bytes=raw(images['msvcrt_staged'],0x78001496,31).hex(),
                 normal_effect=['Push -1 atS-4; metadata atS-8; previous guestFS0 atS-12',
                    'Read original returnword[S] intoEAX, publishFS0=S-12, store priorEBP[S], setEBP=S',
                    'Push original returnword atS-16; actualRET returns to original continuation withESP=S-12'],
                 FS0_effect='Guest chain registration and restore; host FS/TEB never substituted',
                 order_limit='Literal x86 source ordering only; any lifted candidate must independently audit checked-store/read publication order and exceptions'),
             unclosed_source_targets=sorted({e['target_va'] for e in edges if e['disposition']=='direct helper missing dependency closure'}),
             missing_semantic_edges=['Actual selected provider and loader initialization',
                 'TLS/SEH/critical-section/resource service contracts and failure paths',
                 'Factory5432 allocation failure and GlobalAlloc/GlobalLock buffer transitions',
                 'Constructor5665 and complete nested module constructor dependencies',
                 'Allocator/deallocator and factory/thread-slot destruction pairing',
                 'Provider module switching/restoration and exact virtual receiver lifetime'],
             claim_limits=['Selected local CFG completeness is not transitive source dependency completeness.',
                 'Raw file-zero globals are not initialized runtime state.',
                 'Unnamed staged MFC ordinal resolution is identity evidence, not a native implementation.',
                 'No CRT completion, window/menu, rendering/input/audio or completeM4 credit.'])
    validate(doc,images,old,rows)
    rejected=[]
    mutations=[('provider-hash',lambda d:d['images']['mfc42_staged'].__setitem__('sha256','0'*64)),
               ('native-credit',lambda d:d.__setitem__('native_execution_credit',True)),
               ('source-byte',lambda d:d['bodies'][0]['graph']['instructions'][0].__setitem__('bytes','90')),
               ('factory-offset',lambda d:d['source_facts'][0].__setitem__('factory_argument_offset',8)),
               ('receiver-address',lambda d:d['source_facts'][4].__setitem__('receiver_va',0x608c8c)),
               ('gate-order',lambda d:d['gate_order'].reverse()),
               ('guest-SEH',lambda d:d['guest_seh_contract'].__setitem__('FS0_effect','Host FS substitution'))]
    for name,mutation in mutations:
        altered=copy.deepcopy(doc);mutation(altered)
        try:validate(altered,images,old,rows)
        except ValueError:rejected.append(name)
        else:raise ValueError('Actual shared validator admitted '+name)
    out.mkdir(parents=True)
    (out/'inventory.json').write_text(json.dumps(doc,indent=2)+'\n')
    bind(out/'inventory.json')
    for info in files.values():need(digest(Path(info['path']).read_bytes())==info['sha256'],'Final physical source rehash')
    (out/'pins.json').write_text(json.dumps(dict(schema_version=1,files=sorted(files.values(),key=lambda i:i['path'].lower())),indent=2)+'\n')
    report=dict(passed=True,scope=doc['evidence_kind'],inventory_sha256=digest((out/'inventory.json').read_bytes()),
                pins_sha256=digest((out/'pins.json').read_bytes()),selected_local_CFGs=len(bodies),
                selected_instruction_records=sum(b['graph']['instruction_count'] for b in bodies),
                source_edges=len(edges),unclosed_direct_targets=len(doc['unclosed_source_targets']),
                gates=len(gates),shared_validator_denials=rejected,native_execution_credit=False,
                source_implementation_credit=False,actual_loaded_mfc_provider=None)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report=report,report_sha256=digest((out/'report.json').read_bytes()))))


if __name__=='__main__':main()

"""Independent physical four-root/Lockit domain review, without execution credit."""
from __future__ import annotations
from collections import Counter, deque
import hashlib, importlib.util, json, re, struct, sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ROOTS = (0x411010, 0x4DC140, 0x500660, 0x5968F0)
GAME_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
CP_SHA = '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def need(v, s):
    if not v:
        raise ValueError(s)

def main(name):
    out = ROOT / 'reports/m4-lockit-review' / name
    need(not out.exists(), 'Fresh independent static revision required')
    out.mkdir(parents=True)
    pins, counts = {}, Counter()
    def pin(p, h=None):
        p = Path(p).resolve(); actual = sha(p)
        need(h is None or h == actual, 'Exact pinned input ' + str(p))
        need(str(p) not in pins or pins[str(p)] == actual, 'Immutable physical input')
        pins[str(p)] = actual
        return p
    def read(p):
        return json.loads(pin(p).read_bytes())
    def emit(n, value):
        p = out / n; p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8'); pin(p)
    pe_path = pin(ROOT/'tools/analysis/pe.py', 'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec = importlib.util.spec_from_file_location('independent_lockit_PE', pe_path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    game = mod.PEImage(pin(ROOT/'MW3/Mech3.exe', GAME_SHA).read_bytes())
    cp = mod.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL', CP_SHA).read_bytes())
    need(game.image_base == 0x400000 and cp.image_base == 0x780C0000, 'Original preferred PE bases')
    front = ROOT/'reports/m4-lockit-frontier/recovery-r1'
    receipt = read(front/'report.json')
    need(receipt['passed'] and receipt['initializer_credit'] is False, 'Static-only parent')
    for p, h in receipt['files'].items():
        pin(p, h)
    graphs = read(front/'game-normal-graphs.json')
    providers = read(front/'provider-graphs.json')
    shapes = read(front/'root-shapes.json')
    rows = {}
    def physical(pe, r, label):
        code = bytes.fromhex(r['bytes'])
        need(len(code) == r['size'] and 0 < len(code) <= 15, 'Exact instruction size')
        off, _ = pe.rva_range(r['pc'] - pe.image_base, len(code))
        need(pe.read(off, len(code)) == code, 'Physical ' + label + ' instruction ' + hex(r['pc']))
    for g in graphs.values():
        for r in g['instructions']:
            physical(game, r, 'game')
            need(r['pc'] not in rows or rows[r['pc']] == r, 'Consistent overlapping graph boundaries')
            rows[r['pc']] = r
    prows = {}
    for g in providers.values():
        for r in g['instructions']:
            physical(cp, r, 'MSVCP')
            need(r['pc'] not in prows or prows[r['pc']] == r, 'Consistent provider boundary')
            prows[r['pc']] = r
    def relative(r):
        b = bytes.fromhex(r['bytes'])
        if len(b) == 5 and b[0] in (0xE8,0xE9): disp = int.from_bytes(b[1:], 'little', signed=True)
        elif len(b) == 2 and (b[0] == 0xEB or 0x70 <= b[0] <= 0x7F): disp = int.from_bytes(b[1:], 'little', signed=True)
        elif len(b) == 6 and b[0] == 0x0F and 0x80 <= b[1] <= 0x8F: disp = int.from_bytes(b[2:], 'little', signed=True)
        else: raise ValueError('Unsupported direct branch encoding ' + hex(r['pc']))
        target = (r['pc'] + len(b) + disp) & 0xFFFFFFFF
        shown = re.match(r'^0x([0-9a-f]+)', r['operands'])
        need(shown and int(shown[1],16) == target, 'Physical relative branch destination')
        counts['physical_relative_branches'] += 1
        return target
    def local_walk(entry):
        todo, seen = deque([entry]), set()
        while todo:
            pc = todo.popleft()
            if pc in seen: continue
            need(pc in rows, 'Literal local physical closure ' + hex(pc))
            seen.add(pc); r = rows[pc]; m, o = r['mnemonic'], r['operands']; nxt = pc + r['size']
            if m == 'ret': continue
            if m in ('call', 'jmp') or m.startswith('j'):
                if o.startswith('0x'):
                    target = relative(r)
                    if m == 'call': todo.append(nxt)
                    elif m == 'jmp': todo.append(target)
                    else: todo.extend((target,nxt))
                else:
                    need(re.fullmatch(r'dword ptr \[0x[0-9a-f]+\]', o), 'Small roots have only exact memory-IAT indirect transfer')
                    if m == 'call': todo.append(nxt)
                continue
            need(m not in ('int','int3','ud2') and not m.startswith('.'), 'Finite ordinary source instruction')
            todo.append(nxt)
        return seen
    selected_entries, selected_rows, root_evidence = set(), set(), []
    expected_global = {0x411010:0x604E38,0x4DC140:0x60B5C4,0x500660:0x60BFB0,0x5968F0:0x731894}
    callbacks = {0x411010:0x411050,0x4DC140:0x4DC240,0x500660:0x5006C0,0x5968F0:0x596920}
    for root in ROOTS:
        declared = next(x for x in shapes if x['root'] == root)
        todo, entries, reached = deque([root]), set(), set()
        while todo:
            e = todo.popleft()
            if e in entries: continue
            need(str(e) in graphs, 'Physical callee graph exists')
            g = graphs[str(e)]; local = local_walk(e)
            need(local == {r['pc'] for r in g['instructions']}, 'Independent local graph exact equality')
            need(not g['unresolved_controls'], 'No unresolved register transfer in small family')
            entries.add(e); reached.update(local)
            todo.extend(c['target'] for c in g['direct_calls'])
        need(entries == set(declared['entries']) and len(reached)==declared['unique_rows'], 'Independent complete root closure equality')
        off, _ = game.rva_range(declared['slot']-game.image_base,4)
        need(struct.unpack('<I',game.read(off,4))[0] == root, 'Actual original initializer-table DWORD')
        need(declared['registration']['callback']==callbacks[root], 'Literal callback binding')
        allocations = []
        for e in sorted(entries):
            g = graphs[str(e)]; ordered = sorted(g['instructions'],key=lambda r:r['pc'])
            for call in g['direct_calls']:
                if call['target'] != 0x5ABD26: continue
                index = next(i for i,r in enumerate(ordered) if r['pc']==call['site'])
                before = list(reversed(ordered[:index]))
                push = next(r for r in before if r['mnemonic']=='push')
                request = 20 if root == 0x500660 else 24
                need(push['operands']==hex(request) and push['bytes']==('6a14' if request==20 else '6a18'), 'Source PUSH proves distinct requested extent independently of immediate predecessor')
                need(not any(r['mnemonic']=='call' for r in before[:before.index(push)]), 'No call removes actual pending allocation argument')
                allocations.append(dict(CALL_pc=call['site'],PUSH_pc=push['pc'],requested_size=request))
        need(len(allocations)==2, 'Two syntactic owner sites per small root')
        globals_ = {x['address'] for x in declared['absolute_memory_refs']}
        need(expected_global[root] in globals_ and expected_global[root]+4 in globals_, 'Exact shared sentinel and reference globals')
        fs = [rows[x] for x in sorted(reached) if 'fs:[' in rows[x]['operands']]
        need(len(fs)==3 and [r['mnemonic'] for r in fs]==['mov','mov','mov'], 'Three normal game FS operations')
        selected_entries.update(entries);selected_rows.update(reached)
        root_evidence.append(dict(root=root,slot=declared['slot'],entries=sorted(entries),rows=len(reached),bytes=sum(rows[x]['size'] for x in reached),registration=declared['registration'],allocations=allocations,shared_sentinel_global=expected_global[root],shared_reference_global=expected_global[root]+4,FS_sites=fs,actual_BEFORE_globals_known=False,actual_owner_count_known=False))
    need(len(selected_entries)==14 and len(selected_rows)==303 and sum(rows[x]['size'] for x in selected_rows)==1048, 'Exact four-root closure dimensions')
    counts.update(four_roots=4,game_entries=14,game_rows=303,game_bytes=1048,syntactic_MFC24_sites=6,syntactic_MFC20_sites=2,game_FS_sites=12,registration_callbacks=4,provider_full_rows=len(prows),provider_full_bytes=sum(r['size'] for r in prows.values()))
    cpimports={cp.image_base+s['iat_rva']:(d['library'],s['name']) for d in cp.imports() for s in d['symbols'] if 'name' in s}
    gameimports={game.image_base+s['iat_rva']:(d['library'],s['name']) for d in game.imports() for s in d['symbols'] if 'name' in s}
    names={0x78146184:'LeaveCriticalSection',0x7814618C:'InterlockedExchange',0x78146190:'InitializeCriticalSection',0x78146194:'Sleep',0x78146198:'EnterCriticalSection'}
    for a,n in names.items():need(cpimports[a][0].lower()=='kernel32.dll' and cpimports[a][1]==n,'Physical exact provider import '+n)
    need(gameimports[0x5BB4F8][1]=='??0_Lockit@std@@QAE@XZ' and gameimports[0x5BB4F4][1]=='??1_Lockit@std@@QAE@XZ','Physical game/provider named import pair')
    fast=(0x7810A290,0x7810A295,0x7810A296,0x7810A297,0x7810A29A,0x7810A29C,0x7810A306,0x7810A30B,0x7810A311,0x7810A313,0x7810A314,0x7810A315)
    need(sum(prows[x]['size'] for x in fast)==30 and relative(prows[0x7810A29C])==0x7810A306,'Conditional state2 ctor branch exact bytes')
    need(prows[0x7810A311]['bytes']=='8bc7' and prows[0x7810A29A]['bytes']=='8bf9','Source returns entryECX via savedEDI')
    need(prows[0x7810A350]['bytes']=='833d5856147802' and prows[0x7810A357]['bytes']=='750b','Conditional destructor state2 test')
    need(prows[0x7810A359]['bytes']=='6840561478' and prows[0x7810A35E]['bytes']=='ff1584611478' and prows[0x7810A364]['bytes']=='c3','Source VOID destructor does not override EAX')
    initialized=dict(condition='Observed authentic source state78145658==2 and live initialized original CS78145640',constructor_rows=[prows[x] for x in fast],destructor_rows=providers[str(0x7810A350)]['instructions'],game_ctor_slot=0x5BB4F8,game_dtor_slot=0x5BB4F4,provider_state=0x78145658,provider_CS=0x78145640,guest_CS_bytes=24,native_CS_bytes=40,ctor_API_CALL=0x7810A30B,ctor_API_slot=0x78146198,ctor_API_frame_delta=-16,dtor_API_CALL=0x7810A35E,dtor_API_slot=0x78146184,dtor_API_frame_delta=-8,returns_original_ECX=True,destructor_EAX_override_allowed=False,actual_domain_admitted=False,raw_BSS_initialized_identity=False,source_state2_seed_credit=False)
    native_h=pin(ROOT/'tools/m4-crt-locale-batch/locale_batch.hpp')
    native_ops=pin(ROOT/'tools/m4-crt-locale-batch/locale_batch_operations.inc')
    hs=native_h.read_text();ops=native_ops.read_text()
    need('CRITICAL_SECTION native{};' in hs and 'static_assert(sizeof(CRITICAL_SECTION)==40&&alignof(CRITICAL_SECTION)==8)' in ops,'Existing typed native CS resource, not guest-layout cast')
    need('const std::array<unsigned,4>statics{0x78037100,0x78037130,0x78037118,0x780370e8}' in ops and '0x78145640' not in ops,'Existing staticCS admission excludes MSVCP resource')
    controls=[
        'Read-time exact game/provider IATs and full unchanged source-page identities; refuse mismatched targets before API.',
        'Genuine privately initialized MSVCP staticCS association: address, generation, owning thread, depth, live lifecycle; reject opaque guest/native alias casts.',
        'Actual same-thread recursive Enter/Leave lifecycle and measured exports; reject leave at depth0 and held Delete; cleanup exactly once.',
        'Loader state and provider page admission must match authentic original capture; raw BSS0 and seeded2 are not observations.',
        'Invalid state/resource identity, changed permission, import/call-frame corruption, actual private-witness mutation, and failures after partial source object/FS commits each require independent causal attribution.',
        'Capture complete State CPU FX512 ENV28, current whole pages, owner registry and API proofs through denial and retry; demonstrate outside caller hardware and LastError conservation.',
        'Actual original entry/preRET only; any derived postRET/volatile API projection must remain explicitly bounded.',
        'Keep rootcount independent of fixed packed ABI offsets: CPUafter76:116, FXbefore116:628. No text-wide120-to124 substitutions.',
    ]
    emit('four-root-physical.json',root_evidence);emit('initialized-interface.json',initialized);emit('causal-review-plan.json',controls)
    pin(__file__)
    report=dict(passed=True,scope='Independent physical four-small-root closure, exact MSVCP full source and conditional initialized interface; no original/native execution or initializer credit',counts=dict(counts),roots=list(ROOTS),excluded_tree_root=0x4B7F70,excluded_other_Lockit_root=0x4E1CA0,actual_loaded_state_known=False,actual_owner_count_known=False,compiled_probe_checked=False,resource_interface_admitted=False,initializer_credit=0,provider_initialized_path_conditional=True,whole_M4_complete=False,files=pins)
    emit('report.json',report)
    print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=counts)))

if __name__=='__main__':main(sys.argv[1])

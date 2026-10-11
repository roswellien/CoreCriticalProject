"""Independent small genuine tree-prefix and compiled observer review."""
from collections import Counter
import hashlib, importlib.util, json, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def need(v, text):
    if not v:
        raise ValueError(text)


def module(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main(name):
    out = R/'reports/m4-tree-review'/name
    need(not out.exists(), 'Fresh additive independent prefix review')
    out.mkdir(parents=True)
    pins, counts = {}, Counter()
    reader, passed = None, False

    def pin(p, expected=None):
        p = Path(p).resolve(); actual = sha(p)
        need(expected is None or actual == expected, 'Exact physical prefix dependency ' + str(p))
        need(str(p) not in pins or pins[str(p)] == actual, 'Stable reviewed dependency')
        pins[str(p)] = actual
        return p

    def read(p, expected=None):
        return json.loads(pin(p, expected).read_bytes())

    def emit(n, obj):
        p = out/n; p.write_text(json.dumps(obj, indent=2)+'\n', encoding='utf-8'); pin(p)

    try:
        p = R/'reports/m4-tree-original/prefix-preparation-r1'
        b = R/'reports/m4-tree-original/prefix-build-r1'
        e = R/'reports/m4-tree-original/prefix-execution-r1'
        v = R/'reports/m4-tree-original/prefix-validation-r2/report.json'
        validation = read(v, '58e023bb24afc474b164c454bc3591bf2cd476c70b3ce90607251ea67583a920')
        prep = read(p/'report.json', '0ed3a7baf7998b697390041dcf8241c28cc0d8689959c423a72f7971382e39e3')
        build = read(b/'build.json', '051f29c90f0725bd6fd4f7a5145cd9b35f1878c0c903f31a31c2f1d971acc36c')
        execution = read(e/'report.json', '4c8e80ae11e1f792ac45e5db75af59ec853568aa9f464cdd9e6f1776fdaf2e72')
        need(all(x['passed'] for x in (validation,prep,build,execution)), 'Fresh original prefix chain passed')
        need(build['preparation_sha256'] == sha(p/'report.json') and execution['build_sha256'] == sha(b/'build.json') and
             validation['execution_sha256'] == sha(e/'report.json'), 'Exact executed preparation/build/validation lineage')
        need(not prep['predicted_counts_supplied_to_execution'] and prep['original_sequences'] == prep['original_phases'] == 1,
             'Counts observed after one untouched root, not execution inputs')
        for q,h in validation['files'].items(): pin(q,h)
        for f in ('reference.cpp','spec.hpp','protocol.hpp','fs_observer_x86.asm','lockit_observer_x86.asm','preserve_x86.asm','CMakeLists.txt'):
            pin(p/f)
        pe = module(pin(R/'tools/analysis/pe.py'),'tree_prefix_pe')
        game = pe.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        crt = pe.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
        cp = pe.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        worker = pe.PEImage(pin(build['worker'],build['worker_sha256']).read_bytes())
        need(worker.machine == 0x14C, 'Actual x86 original worker')

        def physical(image,a,n):
            return image.read(image.rva_range(a-image.image_base,n)[0],n)

        coff = module(pin(R/'tools/m4-fs-source/observer_attribution.py'),'tree_prefix_coff')
        helpers = module(pin(R/'tools/m4-lockit-review/full_original_review.py'),'tree_prefix_expected_lockit')
        release = b/'build-x86/mw34_joint_startup124_original.dir/Release'
        links = list(release.rglob('link.command.1.tlog'))
        need(len(links) == 1, 'Actual original link command')
        link = pin(links[0]).read_text(encoding='utf-16')
        syms,secs = coff.parse_coff(pin(release/'fs_observer_x86.obj').read_bytes())
        definitions = {s['name']:s for s in syms.values() if s['section']>0 and s['storage']==2}
        need('FS_OBSERVER_X86.OBJ' in link.upper(), 'Current full FS object linked')
        bindings = read(p/'fs-hook-bindings.json')
        need(len(bindings) == 57, 'Current all57 FS observer sites')
        for h in bindings:
            code = bytes.fromhex(h['raw_bytes'])
            need(physical(crt if h['PC'] >= 0x78000000 else game,h['PC'],len(code)) == code, 'Original exact FS replay span')
            expected,rel,_ = coff.expected_function(h['PC'],h['kind'],code)
            name_ = h['declared_observer']; name_ = name_ if name_.startswith('_') else '_'+name_
            d = definitions[name_]; sec = secs[d['section']]
            need(sec['bytes'][d['value']:d['value']+len(expected)] == expected, 'Compiled complete FS observer preservation/replay')
            need([(off-d['value'],n,t) for off,n,t in sec['relocations'] if d['value']<=off<d['value']+len(expected)] == rel,
                 'Every actual FS COFF relocation')
            counts['compiled_FS_functions'] += 1; counts['compiled_FS_bytes'] += len(expected); counts['compiled_FS_relocations'] += len(rel)

        direct = module(pin(R/'tools/m4-crt-allocation-root/run_v2.py'),'tree_prefix_direct')
        transport = read(execution['original_capture'])
        need(transport['payload_bytes'] < 32*1024*1024 and transport['logical_files'] == 112, 'Bounded small prefix capture, no inherited reader')
        reader = direct.DirectSet(execution['original_capture'],pin)
        need(reader.data('COMPLETE.txt') == b'complete', 'Actual complete sealed prefix')
        boot = {a:reader.data(f'lockit/post-DllMain/{a}-page.bin') for a in (0x7810A000,0x78145000,0x78146000)}
        for a,x in boot.items(): need(len(x)==4096 and reader.data(f'lockit/restored/{a}-page.bin')==x,'Full genuine loaded/restored provider pages')
        need(boot[0x7810A000] == physical(cp,0x7810A000,4096), 'Full authentic loaded code page')
        snap = reader.data('phase/0/0/lockit-snapshots.bin')
        need(len(snap)==78*12988 and reader.data('phase/0/0/lockit-count.bin')==struct.pack('<I',78), 'Measured78 boundaries')
        patched,iat = snap[700:4796],snap[8892:12988]
        hooks = read(R/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json')
        lsym,lsec = coff.parse_coff(pin(release/'lockit_observer_x86.obj').read_bytes())
        ldef = {s['name']:s for s in lsym.values() if s['section']>0 and s['storage']==2}
        need('LOCKIT_OBSERVER_X86.OBJ' in link.upper(), 'Actual Lockit object linked')
        functions, linked_symbols = [], {}
        for h in hooks:
            need(physical(cp,h['pc'],h['size']) == bytes.fromhex(h['raw']), 'Whole original provider patch span')
            x = patched[h['pc']&4095:(h['pc']&4095)+h['size']]
            need(x[0]==0xE9 and x[5:]==b'\x90'*(h['size']-5), 'Actual patch padding')
            target = (h['pc']+5+int.from_bytes(x[1:5],'little',signed=True))&0xFFFFFFFF
            functions.append((h['name'].replace('probe_','lockit_'),h['pc'],h['kind'],bytes.fromhex(h['replay']),
                              '_lockit_continue_'+format(h['pc'],'x') if h['continuation'] else None,None,target))
        for name_,kind,cell in (('lockit_api_Enter',1,0x78146198),('lockit_api_Leave',4,0x78146184)):
            functions.append((name_,0,kind,b'',None,'_lockit_actual_'+('Enter' if kind==1 else 'Leave'),struct.unpack_from('<I',iat,cell&4095)[0]))
        for name_,pc,kind,replay,cont,target,linked in functions:
            expected,rel = helpers.expected_lockit(pc,kind,replay,cont,target)
            d = ldef['_'+name_]; sec = lsec[d['section']]
            need(sec['bytes'][d['value']:d['value']+len(expected)] == expected,'Complete actual compiled Lockit observer')
            need([(off-d['value'],n,t) for off,n,t in sec['relocations'] if d['value']<=off<d['value']+len(expected)] == rel,'Exact Lockit COFF relocations')
            actual = physical(worker,linked,len(expected)); normalized = bytearray(actual)
            for offset,symbol,typ in rel:
                addend = struct.unpack_from('<I',expected,offset)[0]; value = struct.unpack_from('<I',actual,offset)[0]
                address = (value-addend)&0xFFFFFFFF if typ==6 else (linked+offset+4+value-addend)&0xFFFFFFFF
                need(symbol not in linked_symbols or linked_symbols[symbol]==address,'Current final linked symbol identity')
                linked_symbols[symbol]=address; normalized[offset:offset+4]=expected[offset:offset+4]
            need(bytes(normalized)==expected,'Complete current final linked Lockit code')
            if cont: need(physical(worker,linked_symbols[cont],4)==struct.pack('<I',pc+len(replay)),'Current linked continuation')
            counts['compiled_linked_Lockit_functions'] += 1; counts['compiled_linked_Lockit_bytes'] += len(expected)
        expected = bytearray(boot[0x7810A000])
        for h in hooks:
            i = h['pc']&4095; expected[i:i+h['size']]=patched[i:i+h['size']]
        need(bytes(expected)==patched,'Only four declared code patches')
        expected = bytearray(boot[0x78146000])
        for cell in (0x78146198,0x78146184):
            i = cell&4095; expected[i:i+4]=iat[i:i+4]
        need(bytes(expected)==iat,'Only two declared API IAT patches')

        graphs = read(R/'reports/m4-lockit-source/complex-plan-r1/game-normal-graphs.json')
        rows = {r['pc']:r for g in graphs.values() for r in g['instructions']}
        scratch = read(R/'reports/m4-lockit-source/complex-next-plan-r1/contracts.json')['Lockit_scratch_contracts']
        affine = {x['CALL_pc']:x['ECX_minus_target_entry_ESP'] for x in scratch}
        returns = {pc+r['size']:pc for pc,r in rows.items() if r['mnemonic']=='call' and
                   (r['operands'] in ('ebp','ebx') or r['operands'] in ('dword ptr [0x5bb4f8]','dword ptr [0x5bb4f4]'))}
        tid = struct.unpack('<I',reader.data('lockit/thread.bin'))[0]
        depth, maximum, active, calls = 0,0,[],[]
        imported = {w[0]:w for w in struct.iter_unpack('<5I',reader.data('lockit/import-ledger.bin'))}
        for start in range(0,78,3):
            rs = [snap[i*12988:(i+1)*12988] for i in range(start,start+3)]
            hs = [struct.unpack_from('<16I',x) for x in rs]
            cpus = [struct.unpack_from('<10I',x,64) for x in rs]
            frames = [struct.unpack_from('<8I',x,644) for x in rs]
            ctor = hs[0][3]==0; kind = 0 if ctor else 3
            need([h[3] for h in hs]==list(range(kind,kind+3)),'Actual three-boundary CALL ordering')
            F,ecx,ret = cpus[0][4],cpus[0][1],frames[0][0]
            need(ret in returns and ecx-F in affine[returns[ret]],'Actual physical caller site and static-affine scratch')
            site = returns[ret]
            need(cpus[0][9] == (0x7810A290 if ctor else 0x7810A350) and
                 cpus[1][9] == imported[0x78146198 if ctor else 0x78146184][1] and
                 cpus[2][9] == (0x7810A311 if ctor else 0x7810A364),'Actual source/API/pre-epilogue PCs')
            need(cpus[1][4]==F-(16 if ctor else 8) and cpus[2][4]==F-(8 if ctor else 0), 'Actual API and pre-epilogue stack relations')
            need(frames[1][:2]==((0x7810A311 if ctor else 0x7810A364),0x78145640),'Actual complete API return/argument')
            if ctor: active.append((F,ecx,site)); newdepth=depth+1
            else:
                need(active and active[-1][1]==ecx,'Actual scratch destructor matches active constructor LIFO')
                newdepth=depth-1
                if site==0x4BADD0: need(active[-1][2]==0x4BAD8F and active[-1][0]==F and ecx-F==24,'Actual normal shared dtor matched scratch; full path trace remains separate')
                active.pop()
            need(newdepth>=0,'No unbalanced actual Leave')
            for j,x in enumerate(rs):
                h,c = hs[j],struct.unpack_from('<6I',x,676); observed=depth if j<2 else newdepth
                need(h[:3]==(1,start+j,0x4B7F70) and h[6:8]==(tid,2), 'Genuine loaded domain/thread')
                need(c==(0xFFFFFFFF,0xFFFFFFFE if observed else 0xFFFFFFFF,observed,tid if observed else 0,0,0x020007D0), 'Complete serial actual CS24')
                need(x[700:4796]==patched and x[8892:12988]==iat,'Full snapshot source/IAT page conservation')
                dp=bytearray(boot[0x78145000]); dp[0x640:0x658]=x[676:700]
                need(x[4796:8892]==dp,'Whole provider data page only actual CS relation')
                counts['actual_Lockit_boundaries'] += 1; counts['whole_provider_snapshot_pages'] += 3
            need(rs[0][104:644]==rs[1][104:644]==rs[2][104:644],'Complete actual FX512 and ENV28 triple')
            calls.append(dict(index=start//3,site=site,frame=F,scratch=ecx,offset=ecx-F,ctor=ctor,before_depth=depth,after_depth=newdepth))
            depth=newdepth;maximum=max(maximum,depth);counts['actual_API_frame_relations']+=1
        need(not active and depth==0 and maximum==2,'Full recursive original LIFO balance')
        counts['actual_Lockit_calls']=len(calls);counts['actual_max_depth']=maximum

        observed_owners = read(v.parent/'actual-owners.json')
        need(len(observed_owners)==7,'Seven measured owners')
        ownerptrs=[]
        for index,owner in enumerate(observed_owners):
            stem=f'phase/0/0/lockit-allocation/{index}'
            meta=struct.unpack('<9I',reader.data(stem+'/meta.bin'))
            final=reader.data(stem+'/bytes.bin'); initial=reader.data(f'phase/0/0/api-initial/{meta[6]}/bytes.bin')
            need(meta==(1,index,0x4B7F70,owner['CALL_pc'],24,owner['source_frame'],owner['actual_API_index'],owner['pointer'],32), 'Exact actual occurrence/meta identity')
            need(final.hex()==owner['final_hex'] and initial.hex()==owner['initial_hex'] and final[24:]==initial[24:], 'Independent complete owner backing/tails')
            ownerptrs.append(meta[7]); counts['actual_owners'] += 1
            need(reader.data(f'cleanup/0/lockit-allocation-{index}-before.bin')==reader.data(stem+'/meta.bin') and
                 reader.data(f'cleanup/0/lockit-allocation-{index}-owned.bin')==final and
                 reader.data(f'cleanup/0/lockit-allocation-{index}-returned.bin')==struct.pack('<I',1),'Actual positive source825 frees')
            counts['actual_positive_owner_frees']+=1
        h,s,n0,n1,n2,n3,n4 = ownerptrs
        expected_fields=[{0:0,4:0,8:0,20:1},{0:n0,4:n1,8:n4,20:0},
                         {0:h,4:n1,8:h,12:0,16:0x5E88CC,20:1},
                         {0:n0,4:s,8:n3,12:1,16:0x5E88C4,20:1},
                         {0:h,4:n3,8:h,12:2,16:0x5E88BC,20:0},
                         {0:n2,4:n1,8:n4,12:3,16:0x5E88B4,20:1},
                         {0:h,4:n3,8:h,12:4,16:0x5E88A8,20:0}]
        for owner,fields in zip(observed_owners,expected_fields):
            expected=bytearray.fromhex(owner['initial_hex'])
            for offset,value in fields.items(): struct.pack_into('<I',expected,offset,value)
            need(bytes(expected).hex()==owner['final_hex'],'Entire actual final tree shape/key/borrowed value/color plus untouched source-unwritten bytes')
            counts['whole_final_owner_images']+=1
        need(reader.data('cleanup/0/registry.bin')==struct.pack('<I',0x4B7FA0),'Actual callback stored, not executed')
        data=reader.data('phase/0/0.bin'); need(len(data)==356992,'Immutable original record ABI')
        pageindex={a:i for i,a in enumerate(prep['observed_pages'])}
        def image(address,after=False):
            base=(178404 if after else 2276)+pageindex[address&~4095]*4096+(address&4095)
            return struct.unpack_from('<I',data,base)[0]
        need(image(0x60B314)==image(0x60B318)==0 and image(0x60B314,True)==h and image(0x60B318,True)==1 and
             image(0x60B2FC,True)==s and image(0x60B304,True)==5,'Untouched BEFORE and measured globals after')
        counts['actual_registration']=1
        emit('actual-API-scratch-joins.json',calls)
        pin(__file__); passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        if reader: reader.close()
        report=dict(passed=passed,scope='Independent bounded genuine one-root prefix, compiled57FS/final-linked6Lockit preservation and actual78 provider boundaries/7 owners/full final tree; no native acceptance',
                    counts=dict(counts), original_validation_sha256=sha(v) if 'v' in locals() else None,
                    original_postRET_observed=False, actual_pre_epilogue_scope=True,
                    instruction_access_trace_consumed=False, shared_branch_full_path_proof_pending=True,
                    initializer_credit=0, inherited_large_reader_opened=False, files=pins)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))


if __name__=='__main__': main(sys.argv[1])

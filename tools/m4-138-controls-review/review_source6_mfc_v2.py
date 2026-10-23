"""Independent current MFC causal byteflow, flag and native API identity joins."""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
_paired_spec=importlib.util.spec_from_file_location('source6_mfc_paired_exports',R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py')
EX=importlib.util.module_from_spec(_paired_spec);_paired_spec.loader.exec_module(EX)

def main(source_path,source_sha,name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    files={};counts=collections.Counter();readers=[];passed=False
    def pin(p,h=None):
        p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip')
        with p.open('rb')as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        assert h is None or h==actual,(p,h,actual)
        assert str(p)not in files or files[str(p)]==actual
        files[str(p)]=actual;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def equal(a,b,s):assert a==b,s
    try:
        source_path=Path(source_path).resolve();source=read(source_path,source_sha)
        assert source['passed']and source['reader_closed']and not source['candidate_AFTER_machine_seed']
        paired_reader=R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py'
        pin(paired_reader,source['files'][str(paired_reader.resolve())])
        def output(n):
            p=source_path.parent/n;return read(p,source['files'][str(p.resolve())])
        rows=output('MFC-source-derivations.json');resources=output('MFC-native-lifecycle-caller.json');proofs=output('MFC-unique-native-API-proofs.json');joins=output('MFC-native-identity-joins.json')
        equal([(r['level'],r['sequence'])for r in rows],[(l,s)for l in('O0','O2')for s in range(6)],'All twelve actual source domains')
        spec=importlib.util.spec_from_file_location('root131_native_physical',pin(R/'tools/m4-mfc1168-native/verify_resource_fixture.py'));V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
        V.PINS={};cache={}
        for proof in proofs:
            path=pin(proof['actual_owner'],proof['physical_sha256']);key=str(path)
            if key not in cache:cache[key]=V.PhysicalPE(path)
            pe=cache[key];w=proof['identity_words'];kind=w[1]
            equal(w[:2],[1,kind],'Actual typed physical owner identity')
            equal(w[6],0x1000,'Committed image backing');equal(w[8],0x1000000,'MEM_IMAGE owning provider')
            assert w[3]>0 and w[4]<=w[2] and w[2]+64<=w[4]+w[5]
            assert w[7]&255 in(0x10,0x20,0x40,0x80)and not w[7]&0x100
            equal(w[2]-w[3],proof['RVA'],'Whole actual target relative owner')
            expected,relocs=pe.entry(proof['RVA'],proof['owner'])
            equal(expected.hex(),proof['entry64'],'Complete physical relocated AMD64 entry64')
            assert any(n in pe.exports and pe.exports[n]['rva']==proof['RVA']and pe.exports[n]['forwarder']is None for n in V.ALIASES.get(kind,[V.NAMES[kind]]))
            counts['independent_physical_native_export_proofs']+=1
        proofs_by_key={(p['identity_words'][1],p['actual_owner'],p['RVA'],p['entry64'])for p in proofs}
        for join in joins:
            assert tuple(join['proof_identity'])in proofs_by_key
            equal(join['kind'],join['call_words'][2],'Actual source lifecycle service kind')
            counts['actual_native_resource_identity_joins']+=1
        for level in('O0','O2'):
            exported=next(r for r in source['paired_exports']if r['branch']==level)
            archive=EX.Facade(exported,pin);readers.append(archive)
            for row in [r for r in rows if r['level']==level]:
                seq=row['sequence'];stem=f'sequence-{seq}/MFC/'
                before=row['source_computed_BEFORE'];memory={int(a):bytearray.fromhex(b)for a,b in before['memory'].items()}
                def get(a,n):
                    owners=[(base,b)for base,b in memory.items()if base<=a and a+n<=base+len(b)]
                    if not owners and (a,n)==(0x7ffde004,8):
                        assert len(memory.get(a,b''))==len(memory.get(a+4,b''))==4
                        return bytes(memory[a])+bytes(memory[a+4])
                    assert len(owners)==1,('Whole computed source owner',hex(a),n)
                    base,b=owners[0];return bytes(b[a-base:a-base+n])
                def put(a,b):
                    owners=[(base,data)for base,data in memory.items()if base<=a and a+len(b)<=base+len(data)]
                    assert len(owners)==1
                    base,data=owners[0];data[a-base:a-base+len(b)]=b
                for label,n in [('State',3504),('CPU',40),('FX',512)]:
                    expected=bytes.fromhex(before[label+'_hex']);equal(len(expected),n,'Whole source-computed entry extent');equal(expected,archive.data(stem+'before/'+label+'.bin'),'Full source-computed current entry')
                regions=list(struct.iter_unpack('<3I',archive.data(stem+'before/memory/index.bin')))
                equal(len(regions),12,'Exact whole current region inventory')
                for a,n,_ in regions:equal(get(a,n),archive.data(stem+f'before/memory/{a}.bin'),'Whole computed current region before')
                witness=row['TIB_region_representation'];equal(len(witness),1,'Exact finite TIB representation witness')
                w=witness[0];equal((w['address'],w['literal_extent']),(0x7ffde004,8),'Exact two DWORD source-only input join')
                equal([(r['address'],r['bytes'])for r in w['original_parts']],[(0x7ffde004,4),(0x7ffde008,4)],'Original carried split inventory')
                equal(get(0x7ffde004,8).hex(),w['joined_BEFORE_hex'],'Whole independently reconstructed TIB BEFORE join')
                equal(''.join(r['BEFORE_hex']for r in w['original_parts']),w['joined_BEFORE_hex'],'Both complete authentic source DWORDs')
                assert not w['candidate_BEFORE_seed']and w['persistent_original_layout_restored']
                events=[tuple(r)for r in row['source_accesses']]
                equal(events,list(struct.iter_unpack('<IIQII',archive.data(stem+'after/accesses.bin'))),'All actual native causal memory operands')
                equal(len(events),113,'Complete finite normal operand count')
                projections={p['access_index']:p for p in row['source_import_projections']}
                assert len(projections)==7
                cursor=0;APIs={r['spec']['source_PC']:r for r in row['source_API_relations']}
                for pc in row['source_PCs']:
                    while cursor<len(events)and events[cursor][0]==pc:
                        _,a,v,n,writing=events[cursor];b=v.to_bytes(n,'little')
                        if writing:put(a,b);counts['independent_literal_source_writes']+=1
                        else:
                            expected=get(a,n)
                            if cursor in projections:
                                p=projections[cursor];equal((pc,a,n),(p['PC'],p['cell'],4),'Exact owning source IAT relation');equal(expected,struct.pack('<I',p['raw']),'Full physical raw IAT preimage');equal(v,p['projected'],'Declared typed source target projection')
                            else:equal(expected,b,'Entire independently reconstructed literal read')
                            counts['independent_literal_source_reads']+=1
                        cursor+=1
                    if pc in APIs:
                        api=APIs[pc]
                        equal(get(api['CPU_before'][4],64).hex(),api['frame64_hex'],'Whole source CALL frame before typed API')
                        for a,b in api['guest_semantic_writes']:put(a,bytes.fromhex(b))
                        counts['typed_guest_semantic_API_relations']+=1
                equal(cursor,113,'All source operands consumed in instruction chronology')
                equal(archive.data(stem+'after/memory/index.bin'),archive.data(stem+'before/memory/index.bin'),'Exact unchanged whole region inventory')
                for a,n,_ in regions:equal(get(a,n),archive.data(stem+f'after/memory/{a}.bin'),'Whole source-derived region endpoint');counts['independent_whole_region_byteflows']+=1
                equal(get(0x7ffde004,8).hex(),w['source_AFTER_joined_hex'],'Whole TIB byteflow after')
                equal(''.join(r['source_AFTER_hex']for r in w['source_AFTER_parts']),w['source_AFTER_joined_hex'],'Inverse complete original split endpoints')
                counts['independent_exact_TIB_join_inverse_relations']+=1
                for owner in row['source_borrowed_backings']:
                    equal(get(owner['new'],owner['extent']).hex(),owner['source_final_hex'],'Whole independent borrowed role byteflow');counts['independent_whole_borrowed_backings']+=1
                equal(bytes.fromhex(row['source_State_hex']),archive.data(stem+'after/State.bin'),'Entire literal final State3504')
                equal(struct.pack('<10I',*row['source_CPU']),archive.data(stem+'after/CPU.bin'),'Entire literal final CPU40')
                equal(bytes.fromhex(row['source_FX_hex']),archive.data(stem+'after/FX.bin'),'Entire preserved guest FX512')
                for consumer in row['defined_flag_consumers']:
                    assert not set(consumer['flags'])&set(consumer['undefined_before'])and consumer['all_consumers_defined']
                    counts['independent_defined_flag_consumers']+=1
                equal([r['PC']for r in row['source_normal_boundaries']],[0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca],'All source-derived normal snapshot PCs')
                counts['source_computed_normal_snapshots']+=7;counts['whole_final_State_CPU_FX']+=1
                lifecycle=next(r for r in resources if (r['level'],r['sequence'])==(level,seq))
                hardware=bytes.fromhex(lifecycle['whole_caller_hardware_hex']);equal(hardware,archive.data(f'sequence-{seq}/MFC-caller-hardware.bin'),'Whole actual outer caller hardware witness')
                equal(hardware[:512],hardware[1088:1600],'Actual full caller FX512 restoration');equal(hardware[512:540],hardware[1600:1628],'Actual full caller ENV28 restoration')
                equal([r['words'][2]for r in lifecycle['events']],[0,2,1,4,2,5,8,6,2,7,1,2,3],'All thirteen actual owned resource services')
                for serial,event in enumerate(lifecycle['events']):
                    equal(tuple(event['words']),archive.words(stem+f'resources/{serial}/call.bin',8,'Q'),'Exact current resource event payload')
                    for suffix in('before','after'):equal(bytes.fromhex(event['CS_'+suffix+'_hex']),archive.data(stem+f'resources/{serial}/CS-{suffix}40.bin'),'Whole actual native CS40 endpoint')
                counts['actual_outer_caller_restorations']+=1
            archive.close();readers.remove(archive)
        for p,h in V.PINS.items():pin(p,h)
        equal(counts['independent_defined_flag_consumers'],132,'Every eleven consumers across twelve source domains')
        equal(counts['independent_whole_region_byteflows'],144,'All whole new regions')
        equal(counts['actual_native_resource_identity_joins'],156,'All actual owned resource service identity joins')
        pin(__file__);pin(paired_reader,source['files'][str(paired_reader.resolve())])
        for p,h in files.items():pin(p,h)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        for archive in readers:archive.close()
        r=dict(passed=passed,source_provider_sha256=source_sha,scope='Independent own computed BEFORE causal full byteflow, finite flag consumers, whole final State/CPU/FX and physical actual native MFC resource identities/caller restoration; raw exported targets only, no canonical archives reopened',counts=dict(counts),files=files,all_bounded_readers_closed=True,capture_archives_opened=0,initializer_credit=0)
        f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])

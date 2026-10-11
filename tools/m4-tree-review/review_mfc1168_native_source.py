"""Independent bounded review of isolated cached-root literal/source/resource observations."""
from pathlib import Path
import hashlib, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
V='25c1085a1cbfbfe9df973715f8e7b5f997876e70fd669de3c02daaf6c30b8bf6'
def need(x,s):
    if not x:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable identity');PINS[str(p)]=v;return p
def load(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def main(name):
    out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Additive output')
    vd=R/'reports/m4-mfc1168-native/fixture-comparison-r1';v=load(vd/'report.json',V)
    need(v['passed']and v['all_bounded_readers_closed']and not v['source_AFTER_seed']and v['initializer_credit']==0,'Current finite isolated source proof')
    for p,h in v['files'].items():pin(p,h)
    pre=load(R/'reports/m4-tree-review/mfc1168-native-prelaunch-r4/report.json','f440e891805bca226f5106d0b33cfef884ad6abcbcc93c753cf06f3347d4289f')
    deps=load(R/'reports/m4-tree-review/mfc1168-native-dependencies-r1/report.json','7b555a669cfc81dab97dc27932687f1bbb429eea527ee8f0fb489064b03eb21e')
    need(pre['passed']and deps['passed'],'Independent physical route/link/consumed-path reviews')
    e=load(v['execution'],v['execution_sha256']);b=load(e['build'],e['build_sha256']);p=load(b['preparation'],b['preparation_sha256'])
    need(e['passed']and e['build_sha256']==pre['build_sha256']and b['preparation_sha256']==pre['preparation_sha256'],'Actual reviewed same fixture compiled/run chain')
    rows=load(vd/'source-derivations.json');need([x['level']for x in rows]==['O0','O2'],'Both actual isolated native levels')
    contracts=load(Path(p['native_contracts']).parent/'contracts.json');program={x['pc']:x for x in contracts['instructions']}
    original=load(R/'reports/m4-mfc1168-probe/validation-r6/source-derivations.json');layout=load(Path(b['preparation']).parent/'before-layout.json')
    need(len(program)==142 and len(layout)==284,'Finite original source and borrowed-input extent')
    counts={'source_instruction_rows':0,'literal_operand_rows':0,'typed_API_CPU_frame_CS40_rows':0,'whole_capacity_byteflows':0,'whole_State_CPU_FX_endpoints':0,'whole_declared_memory_after_extents':0,'actual_native_resource_cleanup_rows':0}
    for row in rows:
        level=row['level'];base=Path(v['execution']).parent/level
        need(row['source_PCs']==original['PCs']and len(row['source_PCs'])==142 and row['call_stack_empty']and row['no_AFTER_seed'],'Exact source path and closed current frames')
        actual=[list(x)for x in struct.iter_unpack('<IIQII',pin(base/'accesses.bin').read_bytes())]
        need(actual==row['source_accesses']and len(actual)==113,'All actual complete source operand tuples/values')
        flags=row['flag_lifetimes'];need(len(flags)==142 and [x['PC']for x in flags]==row['source_PCs'],'Every exact source flag lifetime row')
        for operand in actual:need(operand[0]in program,'No unadmitted source operand PC')
        need(pin(base/'after/State.bin').read_bytes().hex()==row['source_State_hex']and len(bytes.fromhex(row['source_State_hex']))==3504,'Whole current source-derived State3504 target')
        need(pin(base/'after/CPU.bin').read_bytes()==struct.pack('<10I',*row['source_CPU']),'Whole source-derived CPU40 target')
        need(pin(base/'after/FX.bin').read_bytes().hex()==row['source_FX_hex']and len(bytes.fromhex(row['source_FX_hex']))==512,'Whole current FX512 target')
        for block in layout:
            path=base/f'after/blocks/{block["address"]}.bin';need(pin(path).stat().st_size==block['size'],'Every complete declared AFTER extent retained')
            counts['whole_declared_memory_after_extents']+=1
        for owner in row['borrowed_backings']:
            initial=pin(base/f'before/blocks/{owner["guest"]}.bin').read_bytes();final=pin(base/f'after/blocks/{owner["guest"]}.bin').read_bytes()
            need(initial.hex()==owner['initial_hex']and final.hex()==owner['source_final_hex']and len(initial)==len(final)==owner['extent'],'All complete current borrowed capacities, including tails')
            expected=bytearray(initial)
            if owner['role']=='global':expected[20]=0;struct.pack_into('<I',expected,4160,0x421)
            need(expected==final,'Only source-defined global14/1040 publications affect borrowed capacities')
            counts['whole_capacity_byteflows']+=1
        api=pin(base/'APIs.bin').read_bytes();need(len(api)==4*352 and len(row['source_API_relations'])==4,'Complete actual typed four-API boundaries')
        for index,a in enumerate(row['source_API_relations']):
            raw=api[index*352:(index+1)*352];w=struct.unpack_from('<16Q',raw);need(list(w)==a['words'],'Entire current private API witness16Q')
            need(list(struct.unpack_from('<10I',raw,128))==a['before']and list(struct.unpack_from('<10I',raw,168))==a['after'],'Both complete typed guest CPU40 boundaries')
            need(raw[208:272].hex()==a['frame64']and raw[272:312].hex()==a['CS_before']and raw[312:352].hex()==a['CS_after'],'Entire actual source frame64 and nativeCS40 endpoints')
            spec=contracts['normal_APIs'][index];need(w[:5]==(1,index,spec['source_PC'],spec['source_target'],spec['argc']),'Actual exact named guest target/source IAT identity')
            need(w[9]>0 and w[10]!=0xffffffff and w[11]>0,'Actual owned native thread/TLS association identifiers')
            if index==0:need(w[8]==w[11]and w[7]==w[12],'Actual host TLS association and explicitly typed borrowed guest result')
            if index==2:need(w[8]==w[7]==1252,'Actual finite GetACP value')
            after_depth=struct.unpack_from('<I',raw,312+12)[0];actual_owner=struct.unpack_from('<Q',raw,312+16)[0]
            need(after_depth==w[13]and actual_owner==(w[9]if after_depth else 0),'Typed current nativeCS40 depth/owner relationship')
            counts['typed_API_CPU_frame_CS40_rows']+=1
        cleanup=struct.unpack('<8Q',pin(base/'lifecycle.bin').read_bytes());need(cleanup==(1,row['source_API_relations'][0]['words'][9],row['source_API_relations'][0]['words'][10],4,0,1,1,1),'Actual balanced owned native TLS clear/free and CS cleanup witness')
        counts['actual_native_resource_cleanup_rows']+=1;counts['whole_State_CPU_FX_endpoints']+=1;counts['source_instruction_rows']+=142;counts['literal_operand_rows']+=113
    tool=pin(R/'tools/m4-mfc1168-native/compare_fixture.py');text=tool.read_text()
    need('program=program,callbacks={}'in text and 'if m.cursor==0x780014b4:'in text and "self.call_stack[-1][0]==0x5f40107d"in text,'Explicit complete finite program and physical special EH frame handling')
    need("source in input_blocks.items()"in text and "Entire genuine BEFORE input, with actual dispatcher return token only"in text,'Whole actual BEFORE source input joins and only declared Runtime token substitution')
    need('m.api_return(spec[\'source_PC\'],spec[\'argc\'],w[7],transports)'in text and "eq(m.cpu_now(),a['after']"in text,'Bounded typed API result/CS semantic transport only; full return CPU is target')
    need("m=Literal(before_state,before_fx,before_cpu,memory,program=program,callbacks={})"in text,'No native AFTER machine seeds the source model')
    need("bytes(m.state),raw(p/'after/State.bin')"in text and "m.bytes(address,row['size']),raw(p/f'after/blocks/{address}.bin')"in text,'Full source State and complete declared extents checked as AFTER targets')
    # This interpreter receives its complete source program explicitly; its
    # optional inherited source_program() JSON path is not entered here.
    interpreter=pin(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py').read_text()
    need('if program is None:program,callbacks=source_program()'in interpreter,'Unused inherited source inventory branch is explicit')
    pin(R/'tools/m4-formatting-source/flag_domain.py');pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py');pin(__file__);pin(sys.executable)
    out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,comparison_sha256=V,execution_sha256=v['execution_sha256'],
        build_sha256=e['build_sha256'],preparation_sha256=b['preparation_sha256'],counts=counts,
        initializer_credit=0,connected_family_alias_credit=0,native_named_export_body_credit=0,
        actual_caller_hardware_and_negative_credit=0,original_API_volatile_equality_credit=0,
        archive_reader_opened=False,source_AFTER_seed=False,
        scope='Independent bounded source/script/whole retained fixture-output review of the isolated cached-domain O0/O2 root. '
              'Typed TLS/CS40/API representatives and actual finite cleanup are explicit and distinct from original opaque guest resources. '
              'Original volatile registers, native API physical export ownership, complete caller hardware/refusal boundaries and connected130 game-BSS/borrowed-owner alias policy remain separate obligations.',files=PINS),indent=2)+'\n')
    print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),files=len(PINS),counts=counts)))
if __name__=='__main__':main(sys.argv[1])

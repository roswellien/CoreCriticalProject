"""Independent static/build/compiled association; no author comparator imports."""
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-control-carry'
OUT=BASE/'independent-source-r1/closure-r3'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={};CHECKS=[];COMMANDS=[]
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();got=sha(p);need(h is None or h==got,'Exact physical identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting physical identity '+str(p));PINS[str(p)]=got;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def text(p):return pin(p).read_text(encoding='utf-8-sig')
def filemap(p,h=None):
    m=read(p,h);files=m['files']
    for path,value in files.items():pin(path,value['sha256'] if isinstance(value,dict) else value)
    return len(files)
def check(name,**facts):CHECKS.append(dict(name=name,passed=True,**facts))
def run(argv,name):
    argv=list(map(str,argv));r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=ROOT)
    p=OUT/name;p.write_bytes(r.stdout);pin(p);pin(argv[0]);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p),log_sha256=sha(p)))
    need(r.returncode==0,'Independent tooling step '+name);return r.stdout.decode(errors='replace')
def reversed_shared(new,old):
    s=text(new)
    insertion='\n    require(word<std::uint32_t>(domain.fx.data()+28)==0x2ffff&&word<std::uint32_t>(reinterpret_cast<const std::uint8_t *>(&s.x87)+28)==0x2ffff,"Observed carry FX capability mask changed");\n    std::fill_n(domain.fx.data()+28,4,0); // temporary Request only; resident State/FX unchanged'
    special=new.name=='runtime_adapter.cpp'
    if special:need(s.count(insertion)==1,'Only exact two-way Request exception');s=s.replace(insertion,'')
    s=s.replace('m4_crt_control_carry::','m4_mixed::').replace('mw34::m4_crt_control_carry','mw34::m4_mixed').replace('mw34_carry_','mw34_mixed_')
    s=s.replace((ROOT/'tools/m4-crt-control-carry/native_protocol.hpp').as_posix(),(ROOT/'tools/m4-mixed-startup/native_protocol.hpp').as_posix())
    need(s==text(old),'Complete shared source reversal '+str(new));return special
def static_sources(generation):
    old=read(ROOT/'reports/m4-mixed-startup/native-derived-r2/generation.json','eef6604787b10e87b4d9535f390b2c104168daeb9c8bc55306f72e614357414a')
    count=exceptions=0
    for p,h in old['generated_sources'].items():
        p=pin(p,h);new=BASE/'research-r4/native'/p.relative_to(ROOT/'reports/m4-mixed-startup/native-derived-r2')
        exceptions+=reversed_shared(new,p);count+=1
    need(count==29 and exceptions==2,'Complete mixed26 derivative file extent')
    symbols=('__remill_function_return','__remill_jump','__remill_read_memory_32','__remill_write_memory_32','mw34_cf_enter','mw34_cf_load_cw','mw34_cf_store_cw','mw34_cf_wait','mw34_ci_enter')
    def reverse(s):
        for symbol in symbols:s=re.sub(r'\bmw34_carry_control_'+re.escape(symbol)+r'\b',symbol,s)
        return s
    need(reverse(text(BASE/'research-r4/native/control.ll'))==text(ROOT/'reports/m4-crt-control-integration/research-r1/host.ll'),'Exact control IR reversal')
    c=reverse(text(BASE/'research-r4/native/control_context.hpp'))
    for name,path in {'common.hpp':ROOT/'tools/m4-crt-control-integration/common.hpp','runtime.hpp':ROOT/'tools/m4-runtime/runtime.hpp','guest_cw.hpp':ROOT/'tools/m4-guest-cw/guest_cw.hpp','admission.hpp':ROOT/'tools/m4-startup/admission.hpp'}.items():
        c=c.replace('#include "'+path.as_posix()+'"','#include "'+name+'"')
    need(c==text(ROOT/'tools/m4-crt-control-integration/native_context.hpp'),'Exact control Context/include-only reversal')
    need(text(BASE/'research-r4/native/control_capture.hpp').replace('#include "control_context.hpp"','#include "native_context.hpp"')==text(ROOT/'tools/m4-crt-control-integration/state_capture.hpp'),'Exact control State/capture reversal')
    pin(ROOT/'tools/m4-runtime/runtime.hpp','41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536')
    pin(ROOT/'tools/m4-runtime/runtime.cpp','48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7')
    for p,h in generation['original_sources'].items():pin(p,h)
    for p,h in generation['generated_sources'].items():pin(p,h)
    check('All shared numerical/chain/integer sources reverse exactly; control IR and service boundaries unchanged',shared_files=count,integer_Request_exceptions=exceptions,control_external_symbols=len(symbols),runtime_r9_changed=False)
def image_sources():
    parser=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec=importlib.util.spec_from_file_location('read_only_frozen_PE',parser);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()
    provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes()
    pe=module.PEImage(image);dll=module.PEImage(provider)
    matches=[(library['library'],s) for library in pe.imports() for s in library['symbols'] if pe.image_base+s['iat_rva']==0x5bb578]
    need(len(matches)==1 and matches[0][0].lower()=='msvcrt.dll' and matches[0][1].get('name')=='_controlfp','Actual unique game import ownership')
    exports=[x for x in dll.exports() if '_controlfp' in x['names']]
    need(len(exports)==1 and dll.image_base+exports[0]['rva']==0x780042e1 and 'forwarder' not in exports[0],'Actual unique staged provider export')
    mixed=pin(ROOT/'reports/m4-mixed-startup/original-extract-original-build-r2/pages.bin','8edd4512c9af08c7c2da015f0ce5dce090316cdf1b91661d03f83ef56015f62a').read_bytes()
    prior=pin(ROOT/'reports/m4-crt-control-integration/research-r1/pack.bin','135d7d7f8c41ba9a232f2cdc76fb673f9eb52e1939cf70111b3b59cbd6fd91d9').read_bytes()
    pack=pin(BASE/'research-r4/pack.bin','2315499216106d6d1ec84cb102c4061ee215ca7f46655711e771c2fddfa159b3').read_bytes()
    need(len(pack)==106716 and pack[:8]==b'MW4CCP01' and struct.unpack_from('<I',pack,8)==(26,) and pack[12:12+22*4104]==mixed[12:],'Exact initial22 source/data pages unchanged')
    extra=bytearray(prior[12:]);struct.pack_into('<I',extra,8+0x437,(0x410a80-0x5ac43b)&0xffffffff);struct.pack_into('<I',extra,4104+4,0)
    need(pack[12+22*4104:]==extra,'Only authored capture JMP displacement and readonly role change in prior extra pages')
    roles=[struct.unpack_from('<II',pack,12+i*4104) for i in range(26)]
    need(len({x[0] for x in roles})==26 and roles[-4:]==[(0x5ac000,1),(0x5bb000,0),(0x78004000,1),(0x78011000,1)],'Disjoint26-page source pack roles')
    spans=[]
    for source,owner,va,length,page,digest in ((image,pe,0x5ac5a0,19,22,'ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac'),(image,pe,0x5ac5d6,6,22,'cd4225ce0b49983d72e298fad14f78fed9e8bfdc3042de603871ce08a29e3646'),(provider,dll,0x780042e1,303,24,'adf05ce99957b1a9d6c33dce1dda80a595cda795085d2794935bb4d78a46f47b'),(provider,dll,0x7801129b,125,25,'b48e01a7f8be0f6c5f477cb30911f7dc92adcca417894943587560507db19b88')):
        offset=owner.rva_range(va-owner.image_base,length)[0];b=source[offset:offset+length]
        need(hashlib.sha256(b).hexdigest()==digest and b==pack[12+page*4104+8+(va&4095):12+page*4104+8+(va&4095)+length],'Source file/pack range identity')
        section=[s for s in owner.sections if s['virtual_address']<=va-owner.image_base<s['virtual_address']+s['raw_size']]
        need(len(section)==1 and section[0]['readable'] and section[0]['executable'] and not section[0]['writable'],'Actual source RX section')
        spans.append(dict(va=va,bytes=length,file_offset=offset,sha256=digest,section=section[0]['name']))
    need(pe.rva_u32(0x5bb578-pe.image_base)==0x1ded8a,'Original raw control IAT value preserved as guest data')
    check('Exact PE import/export/RX source and additive source-pack association',import_owner=matches[0][0],import_name='_controlfp',raw_iat=0x1ded8a,provider_export=exports[0],source_spans=spans,authored_outer_capture_JMP_target=0x410a80,original_game_RET_continuation=0x5ac436)
def objects(build):
    extent=[];symbols={}
    for level in ('O0','O2'):
        for object_index,(p,h) in enumerate(build['objects'][level].items()):
            p=pin(p,h);name=f'{level}-guest-{object_index}-'+p.stem
            decoded=run([LLVM/'llvm-objdump.exe','-d','-r','--x86-asm-syntax=intel','--print-imm-hex',p],name+'.txt')
            info=run([LLVM/'llvm-readobj.exe','--file-headers','--symbols','--relocations','--unwind',p],name+'-coff.txt')
            need('IMAGE_FILE_MACHINE_AMD64' in info and 'file format coff-x86-64' in decoded,'Actual AMD64 guest object')
            if p.name=='control.obj':
                for s in ('sub_5ac5a0','sub_780042e1','mw34_carry_control_mw34_cf_store_cw','mw34_carry_control_mw34_cf_load_cw','mw34_carry_control___remill_jump'):
                    need(s in info and s in decoded,'Actual compiled typed control relocation '+s)
                need('RuntimeFunction' in info,'Actual Windows control COFF unwind metadata')
            extent.append(dict(level=level,path=str(p),sha256=h,kind='guest LLVM body'))
        directory=ROOT/f'build/m4-crt-control-carry-native-build-r4-{level}'
        candidates=[p for p in directory.rglob('*.obj') if p.name in ('runtime_adapter.cpp.obj','native_main.cpp.obj','runtime.cpp.obj','guest_cw.cpp.obj')]
        need(len(candidates)==5,'Actual compiled C++ boundary/control object extent')
        for index,p in enumerate(candidates):
            pin(p,build['artifacts'][str(p)]);name=f'{level}-boundary-{index}-{p.name}'
            decoded=run([LLVM/'llvm-objdump.exe','-d','-r','--x86-asm-syntax=intel','--print-imm-hex',p],name+'.txt')
            info=run([LLVM/'llvm-readobj.exe','--file-headers','--symbols','--unwind',p],name+'-coff.txt')
            need('IMAGE_FILE_MACHINE_AMD64' in info and 'file format coff-x86-64' in decoded,'Actual AMD64 boundary object')
            if p.name=='runtime_adapter.cpp.obj':need('0x2ffff' in decoded,'Actual emitted resident capability guard immediate')
            if p.name=='native_main.cpp.obj':
                for s in ('mw34_carry_control_mw34_cf_store_cw','mw34_carry_control_mw34_cf_load_cw','mw34_carry_control___remill_jump'):
                    need(s in info,'Actual owning compiled typed control definition '+s)
            extent.append(dict(level=level,path=str(p),sha256=sha(p),kind='C++ boundary'))
    check('Actual compiled AMD64 bodies, relocated bridges, emitted capability guards and Windows unwind information',decoded_objects=len(extent),guest_objects=24,CXX_boundary_objects=10,objects=extent)
def main():
    need(not OUT.exists(),'Fresh independent source closure required');OUT.mkdir(parents=True)
    (OUT/'source_review.py').write_bytes(Path(__file__).read_bytes());pin(OUT/'source_review.py')
    try:
        author=read(BASE/'author-review-r1/report.json','3c58baf0e8a5d2e077d165ae5a0fab85611ac3002ebbee3dfc90c331701a4929')
        total=filemap(BASE/'author-review-r1/pins.json','1c4fbd92e815b5ce082f38d2cde165d64776b9a4010ea33a15854a151198052a')
        need(author['passed'] and total==5643,'Exact final author closure extent')
        for a in author['historical_source_resolutions']:
            m=read(a['historical_map'],a['historical_map_sha256']);sources=m.get('sources',m.get('source_files'))
            need(sources[a['original_path']]==a['recorded_sha256'],'Historical original path association');pin(a['physical_path'],a['recorded_sha256'])
        check('Final author physical closure and all explicit historical source replacements rehashed',author_physical_bindings=total,historical_source_associations=len(author['historical_source_resolutions']))
        generation=read(BASE/'research-r4/generation.json','7d2331768f27efde2efede54e8054a3ca25c3533efd31b48eda2ea170f3e61f5')
        static_sources(generation);image_sources()
        build=read(BASE/'native-build-r4/build.json','4067364cdc78881177541fbaa95c48d950051d8cfc9f2f5e0a343f935c11f1a7')
        for group in ('sources','tools','artifacts'):
            for p,h in build[group].items():pin(p,h)
        for c in build['literal_source_copies']:
            need(c['sha256']==build['sources'][c['original_path']],'Exact before-build source-copy association');pin(c['preserved_path'],c['sha256'])
        supplement=read(BASE/'tooling-supplement-r1/report.json')
        for p,h in supplement['compiler_recorded_dependencies'].items():pin(p,h)
        check('Exact consumed source/tool/artifact and literal before-build source maps; compiler read dependencies',source_count=len(build['sources']),tool_count=len(build['tools']),artifact_count=len(build['artifacts']),compiler_read_dependencies=len(supplement['compiler_recorded_dependencies']),identity_scope='Current post-build hashes bound to recorded commands/read-dependency paths; not execution-time or complete process attestation')
        objects(build)
        own=read(BASE/'independent-source-r1/compiled-r2/report.json','3472c036febcb5c21a0cd6681033ba82862a62a3e6d416dc57dfe0ca4bf7dfd4')
        need(own['passed'] and len(own['results'])==2 and all(r['checks']==1008 and r['scenarios']==42 for r in own['results']),'Exact own fresh compiled causal extent')
        filemap(BASE/'independent-source-r1/compiled-r2/pins.json')
        # Failed own fixture source is literal; its maps retain historical live
        # paths and are bound as artifacts without pretending they still match.
        failed=read(BASE/'independent-source-r1/compiled-r1/report.json');need(not failed['passed'] and 'Protect requires the exact start' in failed['failure'],'Own fixture mistake retained')
        failedpins=read(BASE/'independent-source-r1/compiled-r1/pins.json');ownassociations=[]
        for path,h in failedpins['files'].items():
            if sha(path)==h:pin(path,h)
            else:
                literal=BASE/'independent-source-r1/compiled-r1/literal-sources'/Path(path).name
                pin(literal,h);ownassociations.append(dict(map=str(BASE/'independent-source-r1/compiled-r1/pins.json'),original_path=path,sha256=h,physical_path=str(literal)))
        for p in (BASE/'independent-source-r1/compiled-r1').rglob('*'):
            if p.is_file():pin(p)
        for folder in ('closure-r1','closure-r2'):
            for p in (BASE/'independent-source-r1'/folder).rglob('*'):
                if p.is_file():pin(p)
        check('Independent actual compiled causal boundaries',checks_per_level=1008,scenarios_per_level=42,levels=['O0','O2'],original_or_vendor_execution=False,own_historical_source_associations=ownassociations,own_failed_fixture_attempt='compiled-r1 Protect required mapping start; literal sources/build/log preserved, compiled-r2 changes peer fixture only',own_initial_seal_failures=['closure-r1 original-build map uses source_files; attempted checker source/log retained before schema correction','closure-r2 two old guest objects shared native-O0 basename; decode output collision detected by immutable pin guard. Failed partial log/claimed first command is not accepted. Fresh closure-r3 uses unique object index.'])
        raw=read(BASE/'independent-native-carry-r3/report.json','f174e28679f37ce7f3f78b917901b62ed4cc1f26c7a431b60261ba684d4acf69')
        filemap(BASE/'independent-native-carry-r3/pins.json','e2a1fb354113105402e9ebc743b38f148e195d9ce00d7354641f3418061137a7')
        need(raw['passed'] and raw['counts']['native_phases']==1296,'Exact separately independently modeled raw gate')
        # r2 has a literal checker version and immutable pins; its live checker
        # source entry is explicitly associated with that literal r2 version.
        p=BASE/'independent-native-carry-r2/pins.json';m=read(p)
        associations=[]
        for path,h in m['files'].items():
            h=h['sha256'] if isinstance(h,dict) else h
            if Path(path).resolve()==(ROOT/'tools/m4-crt-control-carry-independent/native_carry.py').resolve():
                physical=BASE/'independent-native-carry-r2/review-source.py';pin(physical,h);associations.append(dict(map=str(p),original_path=path,sha256=h,physical_path=str(physical)))
            else:pin(path,h)
        for p in (BASE/'independent-native-carry-r1').rglob('*'):
            if p.is_file():pin(p)
        need('Entire actual host FX512/ENV28 restoration' in text(BASE/'independent-native-carry-r1/failure.txt'),'Root host-reserved-tail review failure retained')
        check('Separately authored full raw model source/scope checked; final r3 and failed-r1/positive-r2 checker history bound',raw_report_sha256=sha(BASE/'independent-native-carry-r3/report.json'),raw_counts=raw['counts'],root_checker_historical_associations=associations,host_FX_scope='Captured bytes0..415 include all AMD64 XMM0..15; reserved uninitialized tail416..511 is unobserved. ENV28 all checked.',primary_comparator_imported=False)
        report=dict(passed=True,scope='Independent source/build/object and compiled causal closure for actual control-result CW carried into selected26 callbacks; root independently authored full raw model is a distinct bound observation gate',checks=CHECKS,commands=COMMANDS,findings=[],native_roots=27,selected_initializer_roots=26,full_initializer_table_traversed=False,full_CRT_attach_startup=False,frontend_or_menu=False,whole_M4_complete=False,limitations=['Twelve masked incoming CW, empty TOP0/SW0/FTW, installed-image default operands and stable serial borrowers only. No live/nonempty/unmasked/deferred domain admission.','Both resident capability DWORDs must equal measured0x2FFFF; local Request offset28 is mapped to prior fixture0 solely for validator transport. It is not numerical MXCSR/CW/status canonicalization.','Original State/events/routes remain unobserved; root whole-State and event model is independently derived software evidence. Raw dead80 and undefined final condition bits remain observed only.','Original control return projects through authored5AC436 captureJMP410A80; native returns original5AC436. There is no new fullCRT or all144-table orchestration.','Host FX reserved tail416..511 is not a valid hardware restore observation; captured bytes0..415 and full legacyENV28 are bound.','r9 and old service bodies unchanged. Raw GuestMemory failures swallowed by arbitrary user callbacks, arbitrary threading/mapping replacement and concurrent/reparse publication remain outside the trusted serial adapter domain.','Current compiler/SDK hashes and recorded read dependencies are post-build associations, not complete process execution traces.'])
        rp=OUT/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        for p in (ROOT/'tools/m4-crt-control-carry-independent').glob('*'):
            if p.is_file():pin(p)
        for p,h in list(PINS.items()):need(sha(p)==h,'Final unchanged independent association '+p)
        (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(PINS),checks=len(CHECKS),decoded_objects=34,compiled_checks_per_level=1008,compiled_scenarios_per_level=42,report_sha256=sha(rp),pins_sha256=sha(OUT/'pins.json'))))
    except Exception:
        (OUT/'failure.txt').write_text(traceback.format_exc());(OUT/'partial.json').write_text(json.dumps(dict(checks=CHECKS,commands=COMMANDS,bindings=len(PINS)),indent=2));raise
if __name__=='__main__':main()

"""Independent small-file numeric first-writer preparation review, no execution."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, subprocess, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
PSHA='51a2be0b0effd4c9976701ea0fdde26e783049c51f3236b986f2a78c79f78ff4'
BSHA='274ba41792c4789f79bff82c62642c723299604430bf9bc959750c0f7d0edddf'
ISHA='2e06405a753a7cd1ec4fec34f85ea4af0cce5040c250d39b0c5ee3990bea5c8a'
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive consumer');a=sha(p)
    need(h is None or a==h,'Exact physical file '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable immutable input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def module(p,name):
    s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def unpack(path):
    blob=pin(path).read_bytes();need(blob[:8]==b'MW4J124P','Exact input pack magic');n=struct.unpack_from('<I',blob,8)[0];need(len(blob)==12+n*4104,'Whole page input pack')
    rows={}
    for i in range(n):
        a=12+i*4104;page,rights=struct.unpack_from('<2I',blob,a);need(page%4096==0 and page not in rows and rights in(0,1,2),'Bounded unique typed source page');rows[page]=(rights,blob[a+8:a+4104])
    return blob,rows
def main(name):
    out=R/'reports/m4-tree-review'/name;need(re.fullmatch('hypot-fixture-prelaunch-r[1-9][0-9]*',name)and not out.exists(),'Fresh owned output')
    area=R/'reports/m4-hypot-native';folder=area/'fixture-preparation-r3';p=read(folder/'report.json',PSHA)
    build=area/'fixture-build-r3';b=read(build/'build.json',BSHA);inputs=read(p['inputs'],ISHA)
    need(p['passed']and b['passed']and inputs['passed']and b['preparation_sha256']==PSHA
         and Path(b['preparation']).resolve()==(folder/'report.json').resolve(),'Exact current corrected numeric chain')
    for report in(p,b,inputs):
        need(not report['native_executed']and report['initializer_credit']==0,'Unexecuted preparation only')
        for key in('files','artifacts'):
            for f,h in report.get(key,{}).items():
                if Path(f).suffix.lower()not in('.mwb','.zip'):pin(f,h)
    need(inputs['permission_encoding']=={'0':'read execute','1':'read','2':'read write'}and inputs['archive_reader_opened']is False,'One explicit unchanged-payload permission correction')
    old=read(inputs['parent_inputs'],inputs['parent_inputs_sha256']);legacy_folder=R/'reports/m4-hypot-original/prefix-preparation-r2'
    legacy_report=read(legacy_folder/'report.json');_,legacy=unpack(legacy_folder/'pages.bin');need(len(legacy)==119,'Exact inherited legacy page map')
    PE=module(R/'tools/analysis/pe.py','hypot_fixture_PE');providers=[]
    for label,file in [('CRT','MSVCRT.DLL'),('MFC','MFC42.DLL'),('MSVCP','MSVCP50.DLL')]:
        path=pin(R/'local/mw3-staged/Shared_DLLs'/file);providers.append((label,path,PE.PEImage(path.read_bytes())))
    permissions=read(area/'inputs-r4/page-permissions.json');need(len(permissions)==190,'Whole current page permission evidence')
    seeds=pin(area/'inputs-r4/input-state.bin').read_bytes();need(len(seeds)==3480 and seeds==pin(area/'inputs-r3/input-state.bin').read_bytes(),'Whole six genuine BEFORE CPU/FX/ENV inputs unchanged')
    original=R/'reports/m4-hypot-original/prefix-validation-r2';ov=read(original/'report.json','80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313')
    need(ov['passed']and ov['reader_closed']and not ov['numerical_prediction_used'],'Separate actual untraced original BEFORE storage')
    crt_pages=read(original/'actual-CRT-page-endpoints.json');crt_before={(r['sequence'],r['page']):r['before_sha256']for r in crt_pages}
    page_rows=[]
    for case,prior in zip(inputs['cases'],old['cases']):
        seq=case['sequence'];need(seq==prior['sequence']and seq in range(6),'Exact input case lineage')
        raw,now=unpack(pin(case['pack'],case['pack_sha256']));old_raw,before=unpack(pin(prior['pack'],prior['pack_sha256']));need(len(now)==190 and set(now)==set(before),'Whole identical source page inventory')
        allowed=set();changed=0;proof=[]
        for i,(page,(rights,data))in enumerate(sorted(now.items())):
            old_rights,old_data=before[page];need(data==old_data,'Complete genuine4096 BEFORE page conserved')
            if page in legacy:
                expected=legacy[page][0];need(old_rights==expected,'Inherited original legacy rights unchanged');kind='Inherited legacy pack'
            else:
                matches=[q for q in providers if q[2].image_base<=page and page+4096<=q[2].image_base+q[2].size_of_image];need(len(matches)==1,'One exact physical external page owner');label,path,image=matches[0];rva=page-image.image_base
                sections=[s for s in image.sections if s['virtual_address']<=rva<s['virtual_address']+max(s['virtual_size'],s['raw_size'])];need(len(sections)<=1,'One exact section/right source')
                if sections:
                    s=sections[0];expected=2 if s['writable']else 0 if s['executable']else 1
                    expected_old=2 if s['writable']else 1 if s['executable']else 0
                else:
                    need(rva<min(s['virtual_address']for s in image.sections),'Actual physical PE header page');expected=1;expected_old=0
                need(old_rights==expected_old,'Earlier explicit swapped external encoding');kind='Fresh physical provider page'
            need(rights==expected,'Actual worker legacy encoding from own physical header/section')
            if rights!=old_rights:
                changed+=1;allowed.update(range(12+i*4104+4,12+i*4104+8))
            if(page>=0x78000000 and page<0x78040000):need(hashlib.sha256(data).hexdigest()==crt_before[seq,page],'Whole genuine observed CRT BEFORE page digest')
            if page in legacy_report['observed_pages']:
                index=legacy_report['observed_pages'].index(page);record=pin(original/f'raw-observations/case-{seq}-record.bin').read_bytes();expected_bytes=bytearray(record[2276+index*4096:2276+(index+1)*4096])
                if page==0x5bb000:
                    repair=case['reconstructed_IAT'];need(struct.unpack_from('<I',expected_bytes,0x5b0)[0]==repair['observed_value'],'Authentic measured observer IAT input');struct.pack_into('<I',expected_bytes,0x5b0,repair['actual_named_provider'])
                need(data==bytes(expected_bytes),'Whole ordinary root BEFORE page, with only explicit named IAT cell reconstruction')
            proof.append(dict(page=page,kind=kind,rights=rights,sha256=hashlib.sha256(data).hexdigest()))
        need(changed==61 and all(a==bb or i in allowed for i,(a,bb)in enumerate(zip(raw,old_raw))),'Only61 exact permission DWORD tags changed')
        record=pin(original/f'raw-observations/case-{seq}-record.bin').read_bytes();need(len(record)==356992,'Frozen original record ABI')
        need(seeds[seq*580:(seq+1)*580]==record[36:76]+record[116:628]+record[2164:2192],'All580 genuine whole BEFORE input bytes, no AFTER source')
        page_rows.append(dict(sequence=seq,full_page_relations=190,changed_permission_DWORDs=changed,whole_CPU_FX_ENV_BEFORE_bytes=580))
    need(inputs['counts']==dict(inherited_pages=119,fresh_provider_pages=71,changed_permission_tags_per_case=[61]*6),'Exactly measured correction counts')
    prior_review=read(R/'reports/m4-tree-review/hypot-reached-r1/report.json','3695858eeeaaa65a8306777f3355db7535c7ad57325cba0a88c98fce5523f56e')
    need(prior_review['passed']and prior_review['domain_sha256']==p['source_domain_sha256'],'Independent exact reached literal preparation gate')
    bodies=read(area/'reached-domain-r1/literal-bodies.json');trace=read(R/'reports/m4-hypot-original/trace-validation-r2/actual-source-traces.json');accesses=read(R/'reports/m4-hypot-original/trace-validation-r2/actual-source-accesses.json')
    reached=set(map(int,trace[0]['actual_reached_PC_counts']));need(len(reached)==439,'Exact actual source domain')
    expected=[(a['PC'],a['address'],a['width'],int(a['write']))for a in accesses if a['sequence']==0];need(len(expected)==616,'Complete finite source operand chronology')
    for seq in range(6):need([(a['PC'],a['address'],a['width'],int(a['write']))for a in accesses if a['sequence']==seq]==expected,'All six share the literal finite address schedule')
    text=pin(folder/'fixture.cpp').read_text();control=pin(folder/'control_runtime.cpp').read_text();need(text==pin(R/'tools/m4-hypot-native/fixture_v2.cpp').read_text()and control==pin(R/'tools/m4-hypot-native/control_runtime.cpp').read_text(),'Actual frozen compiler inputs')
    for x in('GetCurrentThreadId() == thread','final_return || hf::reached_PC(s.gpr.rip.dword)',
        'e.pc == s.gpr.rip.dword && e.address == a && e.width == n && e.writing == unsigned(writing)',
        'r.memory().read({a},value)','access(a,unsigned(value.size()),true,value); r.memory().write({a},value)',
        'frames.back().address == s.gpr.rsp.dword','a.before = s','a.after = s','s.gpr.rsp.dword == a.frame+4',
        'Unobserved padded source instruction denied','Measured normal empty source stack only',
        'r.register_translation({{0x4b5910},{Abi::Cdecl,0,true},&native_root','r.freeze_registry()',
        'c.frames.empty()&&c.cursor==hf::accesses.size()&&c.API_count==2','r.calls()[0].completed&&!r.poisoned()'):
        need(x in text,'Finite literal source admission '+x)
    need('__asm__ volatile("fldt %1\\n\\tfsqrt\\n\\tfstpt %0"'in text and not any(x in text for x in('std::sqrt','sqrtl(','hypot(')),'Actual raw80 hardware primitive, no host math/numeric oracle')
    need('word != normalized(word) || (word & 63U) != 63U'in control and 'if (actual != word)'in control and '(word & 0x1f3fU) | 0x40U'in control,'Exact fully masked State-authority CW domain')
    for x in('__asm__ volatile("fldcw %0"','state->x87.fxsave.cwd.flat = word','__asm__ volatile("fwait"'):
        need(x in control,'Physical typed x87 control transfer '+x)
    need(text.index('Isolation hw(')<text.index('c.dispatch(0x4b5910,false)')<text.index('hw.close()'),'Explicit isolated literal arithmetic hardware scope')
    need('p.permissions==0?Permissions::read|Permissions::execute:p.permissions==1?Permissions::read:Permissions::read|Permissions::write'in text,'Corrected unified permission enum matches actual worker')
    C=module(R/'tools/m4-tree-review/amd64_coff.py','hypot_fixture_coff');M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','hypot_fixture_image');linked=[];dep_rows=[]
    ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
    for level,w in b['workers'].items():
        bf=Path(w['path']).parent;image=M.AMD64Image(pin(w['path'],w['sha256']).read_bytes());header=pin(bf/'fixture_spec.hpp').read_text();need(header==pin(folder/f'fixture_spec_{level}.hpp').read_text(),'Actual consumed constant header')
        part=re.search(r'array<AccessSpec,616> accesses\{\{(.*?)\}\};',header);need(part,'Explicit compiled finite chronology');rows=[tuple(map(int,a))for a in re.findall(r'\{(\d+)U,(\d+)U,(\d+)U,(\d+)U\}',part[1])];need(rows==expected,'Compiled guard excludes all original output values')
        part=re.search(r'inline bool reached_PC\(unsigned pc\)\{switch\(pc\)\{(.*?)return true;',header);need(part,'Explicit compiled finite PC guard');need(set(map(int,re.findall(r'case (\d+)U:',part[1])))==reached,'All and only439 reached bridge PCs')
        need(pin(folder/'literal_dispatch.hpp').read_bytes()==pin(area/'reached-domain-r1/literal_dispatch.hpp').read_bytes(),'Exact prepared21-body dispatch')
        graph=pin(bf/'build.ninja').read_text();line=next(x for x in graph.splitlines()if x.startswith('build '+Path(w['path']).name+': CXX_EXECUTABLE_LINKER'))
        inputs_link={str((bf/Path(x.replace('$:',':'))).resolve())for x in line.split(' ',3)[3].split(' |')[0].split(' ')if x.endswith('.obj')};need(len(inputs_link)==26 and set(p['objects'][level])<inputs_link,'Actual21 literal and five compiled source objects')
        for body in bodies.values():
            q=body['objects'][level];obj=pin(q['path'],q['sha256']);symbols,sections=C.parse(obj.read_bytes());raw,relocs=C.function(symbols,sections,body['symbol']);matches=C.linked_candidates(image,raw,relocs);need(len(matches)==1,'Unique whole actual linked literal object');linked.append(dict(level=level,entry=body['entry'],linked_address=matches[0][0],whole_function_bytes=len(raw),relocation_DWORDs=len(relocs)))
        control_obj=pin(bf/'CMakeFiles/hypot-native.dir/control_runtime.cpp.obj');symbols,sections=C.parse(control_obj.read_bytes())
        for name_ in('mw34_hypot_store_cw','mw34_hypot_load_cw','mw34_hypot_wait'):
            raw,relocs=C.function(symbols,sections,name_);need(len(C.linked_candidates(image,raw,relocs))==1,'Whole actual compiled typed control helper '+name_)
        fixture_obj=pin(bf/'CMakeFiles/hypot-native.dir/fixture.cpp.obj');symbols,sections=C.parse(fixture_obj.read_bytes());raw,_=C.function(symbols,sections,'mw34_hypot_fsqrt_raw80');need(raw.count(bytes.fromhex('d9fa'))==1,'Actual compiler raw80 function contains one physical FSQRT')
        forbidden={'sqrt','sqrtl','hypot','_hypot','cos','sin','tan'};need(not forbidden&{x['name']for x in symbols.values()if x['section']==0},'No external math replacement imported by actual fixture object')
        for obj in inputs_link:pin(obj)
        db=pin(bf/'.ninja_deps');db_sha=sha(db);result=subprocess.run([str(ninja),'-C',str(bf),'-t','deps'],capture_output=True,creationflags=0x08000000);need(result.returncode==0 and sha(db)==db_sha,'Read-only actual compiler dependency database')
        consumed=[Path(x.strip())for x in result.stdout.decode().splitlines()if x.startswith('    ')and Path(x.strip()).is_file()];need(any(x.resolve()==(folder/'fixture.cpp').resolve()for x in consumed)and any(x.resolve()==(folder/'control_runtime.cpp').resolve()for x in consumed),'Actual separate fixture/control compiler input records')
        for x in consumed:pin(x)
        dep_rows.append(dict(level=level,linked_objects=26,literal_functions=21,control_helpers=3,current_compiler_paths=len(consumed),dependency_database_sha256=db_sha))
    need(all(c['exit_code']==0 for c in b['commands']),'Actual complete successful two-level compiler/link commands')
    controller=pin(R/'tools/m4-hypot-native/run_fixture.py').read_text()
    need("review['files'][str(Path(build_path).resolve())]==build_sha"in controller and 'timeout=30'in controller and 'for level in'in controller and 'for case in'in controller,'Current first-writer controller requires exact independent build edge and finite12-process extent')
    pin(__file__);pin(sys.executable);out.mkdir()
    for filename,value in [('whole-input-relations.json',page_rows),('whole-literal-link-observations.json',linked)]:
        q=out/filename;q.write_text(json.dumps(value,indent=2)+'\n');pin(q)
    report=dict(passed=True,preparation_sha256=PSHA,build_sha256=BSHA,inputs_sha256=ISHA,
        reached_review_sha256=sha(R/'reports/m4-tree-review/hypot-reached-r1/report.json'),counts=dict(genuine_cases=6,
        whole_BEFORE_pages=1140,whole_CPU_FX_ENV_BEFORE_bytes=3480,inherited_rights_pages=119,fresh_rights_pages=71,
        permission_DWORD_changes=366,causal_operand_guards=1232,actual_literal_linked_functions=42,actual_control_linked_helpers=6,bridge_reached_PCs=439),
        levels=dep_rows,worker_launched=False,archive_reader_opened=False,original_AFTER_seed=False,numerical_oracle=False,
        native_source_equivalence=False,caller_hardware_restoration_observed=False,initializer_credit=0,
        scope='Independent first-writer finite smoke prelaunch only. Unified rights, unchanged complete BEFORE input storage, actual source operands/PC '
              'guards, literal object link membership and current compiler dependencies are bound. Guarding occurs at native bridges, not every source '
              'instruction; 233 inherited unreached decoded PCs have no cold-path credit. Native output, independent whole-State/source/backing '
              'comparison, caller restoration, refusal/cleanup and connected-image initializer applicability remain future measured gates.',files=PINS)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),files=len(PINS),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])

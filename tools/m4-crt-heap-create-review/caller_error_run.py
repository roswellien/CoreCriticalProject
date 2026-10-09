"""Execute and seal separate nonzero host-error fixtures with unchanged native source bodies."""
import importlib.util,json,sys,hashlib,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import normalized,unique_object,verify_manifest
from stages import run_stage,verify_stage
from paths import publish_bytes

def need(v,w):
    if not v:raise ValueError(w)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
def main(build_path,name,resume=''):
    build_path=Path(build_path).absolute();base=ROOT/'reports/m4-crt-heap-create-review';out=base/name
    need(name.startswith('caller-error-') and out.parent==base and not out.exists(),'Fresh separate caller-error output');out.mkdir()
    build=read(build_path);need(build['passed'] is True and build['compiled_only'] is True,'Actual independent compiled host-error fixture')
    files={}
    def pin(p,d=None):
        p=Path(p).absolute();a=sha_file(p);need(d is None or a==d,'Current separate caller-error physical dependency');k=normalized(str(p));need(k not in files or files[k]==a,'Conflict-free separate physical proof');files[k]=a;return a
    pin(build_path)
    for category in ('sources','tools','libraries','entry_objects','matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects','locale_objects','heap_objects','compiler_read_headers','artifacts'):
        for p,d in build[category].items():pin(p,d)
    checker=HERE/'check.py';current_check=read(ROOT/'reports/m4-crt-heap-create-review/check-r2/pins.json');pin(checker,current_check['files'][normalized(str(checker))])
    spec=importlib.util.spec_from_file_location('frozen_current_hardware_schema',checker);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    validator,association=C.T.load_validator();requests=[0,0,121,122,132,39];levels={};pairs=creates=destroys=0
    for level in ('O0','O2'):
        worker=build_path.parent/level/'controls.exe';reuse=bool(resume and (Path(resume)/('native-'+level)/'stage.json').is_file());location=Path(resume).absolute() if reuse else out;tree=location/('actual-'+level);stage=location/('native-'+level)
        argv=[str(worker),str(ROOT/'MW3/Mech3.exe'),str(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj'),str(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),str(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin'),str(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin'),str(tree)]
        record=read(stage/'stage.json') if reuse else run_stage(argv,stage,timeout_seconds=180,required_outputs=[tree/'COMPLETE',tree/'controls.json'],inputs=list(files));verify_stage(stage,sha_file(stage/'stage.json'));need(record['passed'] is True and record['argv']==argv,'Actual separate caller-error native execution')
        for n in ('stage.json','stdout.bin','stderr.bin'):pin(stage/n)
        result=read(tree/'controls.json');need(result['passed'] is True and result['scenarios']==6 and result['malformed_token_denials']==0,'Exact independent nonzero-error request corpus')
        bundle=location/(level+'.mwb');pack=location/('pack-'+level);pr=read(pack/'stage.json') if reuse else run_stage([sys.executable,str(ROOT/'tools/m4-pipeline/capture_bundle.py'),'pack',str(tree),str(bundle)],pack,timeout_seconds=180,required_outputs=[bundle],inputs=list(files));verify_stage(pack,sha_file(pack/'stage.json'));need(pr['passed'] is True,'Strict separate caller-error bundle')
        for n in ('stage.json','stdout.bin','stderr.bin'):pin(pack/n)
        digest=pin(bundle);inventory={}
        with CaptureBundle(bundle,digest) as b:
            for n in b.names():
                data=b.read_bytes(n);inventory[n]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
            logical=C.T.LogicalReader({n:{'size_bytes':v['bytes'],'sha256':v['sha256']} for n,v in inventory.items()},bundle=b)
            expected={'COMPLETE','controls.json'}
            for number,mode in enumerate(requests,1):
                case=f'case-{number}';need(C.struct.unpack('<I',b.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Exact separate request order')
                s=C.struct.unpack('<32I',b.read_bytes(case+'/heap-status.bin'));need(s[23]==s[24]==0xbeef0000+number and s[13]==0 and s[22]==1,'Actual nonzero scheduler LastError restored and ownership closed')
                w=C.struct.unpack('<16Q',b.read_bytes(case+'/heap-witness.bin'));need(w[8]==w[10]==0xbeef0000+number and w[:6]==(1,int(mode==121),int(mode!=121),0,4096,0),'Actual incoming/restored API error reads and declared NULL seam')
                own=C.struct.unpack('<8Q',b.read_bytes(case+'/independent-ownership.bin'));need(own[1:6]==(int(mode!=121),)*5 and own[6:]==(1,0) and bool(own[0])==(mode!=121),'Actual owned live heap, exact successful release and idempotent closed cleanup')
                r=C.struct.unpack('<18Q',b.read_bytes(case+'/heap-registry.bin'));need(r[7]==0 and r[9]==r[10]==int(mode!=121) and r[16]==own[0],'Exact private full-HANDLE cleanup input and result')
                phases=set(C.BASE_PHASES)
                for modes,n in ((C.PROVIDER,'heap-create-provider-before'),(C.API,'heap-create-api-before'),(C.RETURN_BEFORE,'heap-create-api-return-before'),(C.RETURNED,'heap-create-api-returned'),(C.PUBLISHED,'heap-create-published'),(C.MODE,'heap-create-mode-before'),({121},'heap-create-zero-before')):
                    if mode in modes:phases.add(n)
                expected|={case+'/'+n for n in C.CASE_FILES}
                for phase in phases:expected|={case+'/'+phase+'/'+n for n in C.PHASE_FILES}
                for actor in ('writer','entry'):
                    validator(logical.path(case+'/'+actor+'-host-before.bin'),logical.path(case+'/'+actor+'-host-after.bin'),number);pairs+=1
                creates+=int(mode!=121);destroys+=own[5]
            need(b.names()==tuple(sorted(expected)) and b.read_bytes('COMPLETE')==b'COMPLETE','Exact separate whole case/phase/file inventory')
            C.T.validate_inventory(b,{n:{'size_bytes':v['bytes'],'sha256':v['sha256']} for n,v in inventory.items()})
        inv=out/(level+'-inventory.json');publish_bytes(inv,(json.dumps({'files':inventory},indent=2)+'\n').encode());pin(inv)
        levels[level]={'worker':str(worker),'worker_sha256':sha_file(worker),'argv':argv,'native_stage':str(stage),'native_stage_sha256':sha_file(stage/'stage.json'),'native_seconds':record['elapsed_seconds'],'result':result,'bundle':str(bundle),'bundle_sha256':digest,'logical_files':len(inventory),'inventory_path':str(inv),'inventory_sha256':sha_file(inv),'pack_stage':str(pack),'pack_stage_sha256':sha_file(pack/'stage.json'),'pack_seconds':pr['elapsed_seconds']}
    need(pairs==24 and creates==destroys==10,'Complete separate nonzero-error ownership/hardware proof')
    for p,d in C.T.SOURCES.items():pin(p,d)
    for p in (Path(__file__),HERE/'caller_error_generate.py',Path(sys.executable),ROOT/'tools/m4-pipeline/stages.py',ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
    closure=verify_manifest(files)
    report={'passed':True,'scope':'Separate explicitly authored host LastError seed after real mainargs-before checkpoint and before exact immutable candidate heap scheduler; no guest mutation or source-causal oracle','compiled_path':str(build_path),'compiled_sha256':sha_file(build_path),'requests':requests,'levels':levels,'native_scenarios':12,'native_checks':sum(i['result']['checks'] for i in levels.values()),'actual_hardware_pairs':24,'actual_HeapCreate_calls':10,'actual_successful_HeapDestroy_calls':10,'incoming_nonzero_error_prefix':0xbeef0000,'source_or_candidate_changed':False,'original_executed':False,'ordinary_game_launched':False,'heap_initialized':False,'full_causal_source_model_oracle':False,'whole_M4_complete':False,'validator':association,'physical_closure':closure,'files':files}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'native_checks':report['native_checks'],'native_scenarios':12,'hardware_pairs':24}))
if __name__=='__main__':main(*sys.argv[1:])

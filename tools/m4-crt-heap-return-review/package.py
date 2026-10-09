"""Publish bounded strict archives from existing passed native stages; never rerun them."""
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import normalized,unique_object,verify_manifest
from stages import run_stage,verify_stage
from paths import publish_bytes

def need(ok,why):
    if not ok:raise ValueError(why)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def main(compiled,source_name,name):
    build_path=Path(compiled).absolute();base=ROOT/'reports/m4-crt-heap-return-review';source=base/source_name;out=base/name
    need(source.parent==base and out.parent==base and name.startswith('native-') and not out.exists(),'Original immutable native tree and fresh publication namespace');out.mkdir();files={};levels={}
    build=read(build_path);need(build['passed'] is True and build['compiled_only'] is True,'Frozen passed independent compile')
    def pin(p,h=None):
        p=Path(p).absolute();value=sha_file(p);need(h is None or h==value,'Exact physical packaging association '+str(p));key=normalized(str(p));need(key not in files or files[key]==value,'Conflict-free packaging dependency');files[key]=value;return value
    pin(build_path,'c5b05ccb5be8f41d547fd6d1f0f452cc5b5bd082b037f77d5f036386f0256402')
    for p in (Path(__file__),HERE/'partition.py',Path(sys.executable),ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/m4-pipeline/stages.py',ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
    for category in ('sources','tools','libraries','entry_objects','matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects','locale_objects','heap_objects','heap_mode_objects','heap_version_objects','compiler_read_headers','artifacts'):
        for p,h in build[category].items():pin(p,h)
    for level in ('O0','O2'):
        stage=source/('run-'+level);stage_sha=pin(stage/'stage.json');verify_stage(stage,stage_sha);row=read(stage/'stage.json');need(row['passed'] is True,'Passed immutable native stage')
        for p,h in row['input_sha256'].items():pin(p,h)
        for filename in ('stdout.bin','stderr.bin'):pin(stage/filename)
        tree=source/('actual-'+level);controls=tree/'controls.json';complete=tree/'COMPLETE'
        for p in (controls,complete):pin(p,row['artifact_sha256'][str(p)])
        result=read(controls);need((complete).read_bytes()==b'COMPLETE' and result['passed'] is True and result['checks']==7521 and result['scenarios']==122 and result['malformed_token_denials']==22 and result['direct_host_failure_queries']==2,'Exact completed independent native corpus')
        info={'worker':row['argv'][0],'worker_sha256':sha_file(row['argv'][0]),'argv':row['argv'],'native_stage':str(stage),'native_stage_sha256':stage_sha,'native_seconds':row['elapsed_seconds'],'result':result,'source_tree':str(tree),'source_controls':str(controls),'source_controls_sha256':sha_file(controls),'source_complete':str(complete),'source_complete_sha256':sha_file(complete),'bundles':[]}
        view=out/('links-'+level);manifest=out/(level+'-partition-map.json');part_stage=out/('partition-'+level)
        record=run_stage([sys.executable,str(HERE/'partition.py'),str(tree),str(view),str(manifest)],part_stage,timeout_seconds=600,required_outputs=[manifest],inputs=list(files))
        verify_stage(part_stage,sha_file(part_stage/'stage.json'));need(record['passed'] is True,'Fresh immutable hardlink partitioning')
        for filename in ('stage.json','stdout.bin','stderr.bin'):pin(part_stage/filename)
        pin(manifest);mapping=read(manifest);need(mapping['passed'] is True and mapping['source_files_modified'] is False and mapping['transport_limit_unchanged']==200000,'Bounded source-preserving partition receipt')
        inventory={}
        for part in mapping['parts']:
            part_id=part['part'];bundle=out/(level+'-part-'+str(part_id)+'.mwb');pack_stage=out/('pack-'+level+'-'+str(part_id));pack_source=part['pack_source']
            record=run_stage([sys.executable,str(ROOT/'tools/m4-pipeline/capture_bundle.py'),'pack',pack_source,str(bundle)],pack_stage,timeout_seconds=600,required_outputs=[bundle],inputs=list(files))
            verify_stage(pack_stage,sha_file(pack_stage/'stage.json'));need(record['passed'] is True,'Unchanged strict bounded capture publication')
            for filename in ('stage.json','stdout.bin','stderr.bin'):pin(pack_stage/filename)
            digest=pin(bundle)
            with CaptureBundle(bundle,digest) as reader:
                need(reader.names()==tuple(sorted(part['files'])),'Exact native-to-part closed inventory')
                for logical in reader.names():
                    data=reader.read_bytes(logical);actual={'bytes':len(data),'sha256':__import__('hashlib').sha256(data).hexdigest()};need(actual==part['files'][logical] and logical not in inventory,'Exact original-relative path/extent/SHA and disjoint union');inventory[logical]=actual
            part_inventory=out/(level+'-part-'+str(part_id)+'-inventory.json');publish_bytes(part_inventory,(json.dumps({'files':part['files']},indent=2)+'\n').encode());pin(part_inventory)
            info['bundles'].append({'part':part_id,'bundle':str(bundle),'bundle_sha256':digest,'logical_files':part['logical_files'],'inventory_path':str(part_inventory),'inventory_sha256':sha_file(part_inventory),'pack_stage':str(pack_stage),'pack_stage_sha256':sha_file(pack_stage/'stage.json'),'pack_seconds':record['elapsed_seconds'],'pack_source':pack_source})
        need(inventory==mapping['files'] and len(inventory)==mapping['logical_files'],'Whole native tree equals exact archive-part union')
        inventory_path=out/(level+'-inventory.json');publish_bytes(inventory_path,(json.dumps({'files':dict(sorted(inventory.items()))},indent=2)+'\n').encode());pin(inventory_path)
        info.update(logical_files=len(inventory),inventory_path=str(inventory_path),inventory_sha256=sha_file(inventory_path),partition_map=str(manifest),partition_map_sha256=sha_file(manifest),partition_stage=str(part_stage),partition_stage_sha256=sha_file(part_stage/'stage.json'));levels[level]=info
    refusal=base/'packaging-refusal-r1/report.json';refusal.parent.mkdir();failed=source/'pack-O0';failed_stage=read(failed/'stage.json');need(failed_stage['passed'] is False and 'Capture count exceeds limit' in (failed/'stderr.bin').read_text(),'Original aggregate publication refusal retained')
    histories={}
    for p in (failed/'stage.json',failed/'stdout.bin',failed/'stderr.bin'):
        histories[normalized(str(p))]=pin(p)
    history={'passed':False,'current_proof_credit':False,'native_fixture_O0_passed':True,'native_fixture_O2_passed':True,'native_rerun':False,'reason':'Both completed native fixture trees passed, but first aggregate strict publication exceeded the unchanged 200000-entry transport limit before hardware checking. Fresh disjoint archives preserve the same original logical tree.','files':histories}
    publish_bytes(refusal,(json.dumps(history,indent=2)+'\n').encode());pin(refusal)
    closure=verify_manifest(files)
    report={'passed':True,'scope':'Adopt the same passed immutable native O0/O2 stages and publish their exact disjoint bounded archive union; no native rerun','compiled_path':str(build_path),'compiled_sha256':sha_file(build_path),'source_native_namespace':str(source),'source_native_stages_immutable':True,'native_rerun':False,'archive_partitioning_only':True,'levels':levels,'native_scenarios':244,'native_checks':15042,'malformed_token_denials':44,'counterfactual_direct_host_failure_queries':4,'original_executed':False,'ordinary_game_launched':False,'native_executed':False,'adopts_actual_native_execution':True,'HeapCreate_executed':False,'GetVersionExA_executed':False,'validates_actual_native_GetVersionExA':True,'genuine_source_token_published':True,'full_heap_initialization_complete':False,'synthetic_API_results':False,'declared_lower_stack_inputs':6,'probe_return_proved':True,'full_causal_source_model_oracle':False,'table_initialization_proved':False,'whole_M4_complete':False,'publication_refusal_history':str(refusal),'publication_refusal_sha256':sha_file(refusal),'closure':closure,'files':files}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'native_scenarios':244,'native_checks':15042,'logical_files':{level:info['logical_files'] for level,info in levels.items()}}))

if __name__=='__main__':main(*sys.argv[1:])

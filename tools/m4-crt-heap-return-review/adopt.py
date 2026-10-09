"""Bind bounded packaging and preserved refusals to the same immutable native stages."""
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,unique_object,verify_manifest
from stages import verify_stage
from paths import publish_bytes

def need(ok,why):
    if not ok:raise ValueError(why)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def main(source_name,name):
    base=ROOT/'reports/m4-crt-heap-return-review';source=base/source_name/'report.json';out=base/name;packaging=base/'packaging-r1/report.json';history=base/'hardlink-refusal-r1/report.json'
    need(name.startswith('native-') and out.parent==base and not out.exists() and not packaging.exists() and not history.exists(),'Fresh immutable adoption/packaging/history receipts');out.mkdir();packaging.parent.mkdir();history.parent.mkdir()
    original=read(source);need(original['passed'] is True and original['native_rerun'] is False and original['archive_partitioning_only'] is True and original['native_checks']==15042,'Same completed native stages and bounded publication')
    files=dict(original['files'])
    def pin(p,h=None):
        p=Path(p).absolute();d=sha_file(p);need(h is None or h==d,'Exact adoption association');key=normalized(str(p));need(key not in files or files[key]==d,'Conflict-free adoption identity');files[key]=d;return d
    pin(source);pin(Path(__file__));pin(HERE/'partition_copy.py');pin(HERE/'package_copy.py')
    levels={}
    for level,info in original['levels'].items():
        verify_stage(info['native_stage'],info['native_stage_sha256']);native=read(Path(info['native_stage'])/'stage.json')
        need(native['passed'] is True and info['source_tree']==native['argv'][-1]==info['argv'][-1],'Original immutable native stage source association')
        for key in ('source_controls','source_complete'):pin(info[key],info[key+'_sha256']);need(native['artifact_sha256'][info[key]]==info[key+'_sha256'],'Original closed native output identity')
        pin(info['partition_map'],info['partition_map_sha256']);mapping=read(info['partition_map'])
        need(mapping['passed'] is True and mapping['source_files_modified'] is False and mapping['hardlinks_only'] is False and mapping['byte_identical_copies_only'] is True and mapping['transport_limit_unchanged']==200000 and mapping['original_relative_paths_preserved'] is True,'Exactly verified byte-identical private copies; original data unchanged')
        whole=read(info['inventory_path'])['files'];need(whole==mapping['files'],'Exact complete original relative-path/SHA union')
        union={}
        for mapped,part in zip(mapping['parts'],info['bundles']):
            verify_stage(part['pack_stage'],part['pack_stage_sha256']);stage=read(Path(part['pack_stage'])/'stage.json')
            need(stage['passed'] is True and stage['argv']==[str(Path(sys.executable)),str(ROOT/'tools/m4-pipeline/capture_bundle.py'),'pack',part['pack_source'],part['bundle']],'Literal unchanged strict pack invocation')
            need(mapped['pack_source']==part['pack_source'] and mapped['part']==part['part'] and len(mapped['files'])==part['logical_files']<=200000,'Exact original-to-part binding within unchanged limit')
            for logical,row in mapped['files'].items():need(logical not in union,'No duplicate native logical records');union[logical]=row
        need(union==whole and len(union)==info['logical_files'],'Exact disjoint native inventory union')
        levels[level]={key:info[key] for key in ('source_tree','native_stage','native_stage_sha256','source_controls','source_controls_sha256','source_complete','source_complete_sha256','inventory_path','inventory_sha256','logical_files','partition_map','partition_map_sha256','partition_stage','partition_stage_sha256','bundles')}
        levels[level].update(byte_identical_private_copies=True,copy_verified=True)
    pack_report={'passed':True,'native_rerun':False,'transport_limits_changed':False,'transport_MAX_FILES':200000,'byte_identical_private_copies':True,'copy_verified':True,'hardlinks_only':False,'partition_tool_path':str(HERE/'partition_copy.py'),'partition_tool_sha256':sha_file(HERE/'partition_copy.py'),'packager_tool_path':str(HERE/'package_copy.py'),'packager_tool_sha256':sha_file(HERE/'package_copy.py'),'source_packaging_path':str(source),'source_packaging_sha256':sha_file(source),'levels':levels,'files':files,'native_executed':False,'original_executed':False,'hardware_success_credit':False}
    publish_bytes(packaging,(json.dumps(pack_report,indent=2)+'\n').encode());pin(packaging)
    failed=base/'native-r2/partition-O0';stage=read(failed/'stage.json');need(stage['passed'] is False and stage['inputs_stable'] is True and 'PermissionError: [WinError 5]' in (failed/'stderr.bin').read_text(),'Original hardlink denial before first capture link preserved')
    histories={}
    for p in (failed/'stage.json',failed/'stdout.bin',failed/'stderr.bin',HERE/'partition.py',HERE/'package.py'):histories[normalized(str(p))]=pin(p)
    failure={'passed':False,'current_proof_credit':False,'native_rerun':False,'reason':'Windows rejected creation of the first NTFS hardlink before any source capture file was linked. A fresh owned namespace used SHA-verified byte-identical copies of the same completed native trees.','files':histories,'native_executed':False}
    publish_bytes(history,(json.dumps(failure,indent=2)+'\n').encode());pin(history)
    report=dict(original);report.update(scope='Same immutable native O0/O2 execution with independently bound bounded strict packaging; adoption only, no native rerun',packaging_path=str(packaging),packaging_sha256=sha_file(packaging),hardlink_refusal_history=str(history),hardlink_refusal_sha256=sha_file(history),source_packaging_path=str(source),source_packaging_sha256=sha_file(source),files=files,closure=verify_manifest(files))
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'packaging_sha256':sha_file(packaging),'hardlink_refusal_sha256':sha_file(history),'native_rerun':False}))

if __name__=='__main__':main(*sys.argv[1:])

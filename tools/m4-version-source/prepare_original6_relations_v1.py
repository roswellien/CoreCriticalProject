"""Additive original6 provenance correction and actual linked method inventory."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 d=json.loads(pin(R/'reports/m4-version-source/original-preparation-r6/report.json','37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6').read_bytes());relations=[]
 for x in d['source_relations']:
  parent=pin(x['parent']);child=pin(x['child']);relations.append(dict(parent=str(parent),child=str(child),parent_sha256=sha(parent),sha256=sha(child),unchanged=parent.read_bytes()==child.read_bytes(),declared_before_correction=x))
 c=next(x for x in relations if Path(x['child']).name=='contracts.json');a=json.loads(Path(c['parent']).read_bytes());b=json.loads(Path(c['child']).read_bytes());delta={k:dict(before=a.get(k),after=b.get(k))for k in a.keys()|b.keys()if a.get(k)!=b.get(k)}
 assert delta=={k:dict(before=None,after=True)for k in ('actual_loaded_and_expected_provider_whole_file_IDs','independent_same_physical_provider_file_equivalence','raw_loaded_provider_paths_retained')};c['exact_JSON_delta']=delta
 build=json.loads(pin(R/'reports/m4-version-source/original-build-r6/build.json','cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7').read_bytes());m=pin(R/'reports/m4-version-source/original-build-r6/original-worker.map',build['files'][str((R/'reports/m4-version-source/original-build-r6/original-worker.map').resolve())]);rows=m.read_text().splitlines();methods=[]
 for token,address in [('?version_load_isolated_provider@@YAXXZ','1800e9b0'),('?version_provider_file_ID@@','1800ff30'),('?version_emit_isolated_provider@@','1800dd50'),('??1Context@?1??version_load_isolated_provider@@','18004710'),('??1File@?1??version_provider_file_ID@@','18004730'),('?version_module_path@@','1800fcb0'),('___std_fs_equivalent@8','1802c740')]:
  matches=[x for x in rows if token in x and '0001:'in x and address.lower()in x.lower()];assert len(matches)==1,(token,matches);methods.append(dict(token=token,address=int(address,16),actual_MAP_row=matches[0],out_of_line=True))
 pin(__file__);out.mkdir(parents=True);report=dict(passed=True,scope='Additive exact whole-file original6 source relation correction and actual linked provider inventory; no worker/capture reads',corrected_relation_reason='contracts.json received three explicit file identity keys after the copy relation was collected; full files closure was already correct',frozen_preparation_or_worker_changed=False,whole_source_relations=relations,contract_keys_added=3,out_of_line_methods=methods,inlined_wrapper='std::filesystem::equivalent wrapper has no distinct MAP entry; its selected backend is the recorded ___std_fs_equivalent@8',File_destructor_folded_with_existing_version_actual_file_destructor=True,original_executed=False,native_executed=False,archive_reader_opened=False,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main(sys.argv[1])

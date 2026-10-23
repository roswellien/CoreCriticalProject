"""Seal current strict3 ordinary tree inputs; ROOT admission remains separate."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-original141-tree-source/admission-recipe-r2';out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def report(p,h):
  p=pin(p,h);j=json.loads(p.read_bytes());assert j['passed']
  for f,v in j['files'].items():pin(f,v)
  return p,j
 prep,prepared=report(R/'reports/m4-original141-tree-source/closure-preparation-r1/report.json','c12647c250cc491c42e31dc52b425c2194f096ba70337c1da2ce070fcf628952')
 review,reviewed=report(R/'reports/m4-original141-tree-source/preflight-r1/report.json','6c4dae4c42ac92f887dacf987f5f97ce05cc7af82a557a01f5660a553e17fde9');assert reviewed['controls']==18 and reviewed['exact_eleven_delta_inverse']
 source,sourceprep=report(R/'reports/m4-original141-tree-source/preparation-r2/report.json','4cb5546572cfde539fcf20bc66eabf0d982155a77349bef8d0ac8e936c6bb41d')
 child=R/'tools/m4-original141-tree-source/tree_source_v3.py';s=pin(child).read_text(encoding='utf-8');inverse=s
 boundary,boundary_gate=report(R/'reports/m4-original141-tree-source/ordinary-boundary-preparation-r1/report.json','6a2656e3c55d00d931e3abfdccc8f39beec643716fd997fe9a46628593a1019b')
 controls,control_gate=report(R/'reports/m4-original141-tree-source/ordinary-boundary-controls-r1/report.json','ba5f7efdf71cba46f591fe56db0f8154074db7bfb5d1edb25679658ddf69dfdc')
 for d in reversed(json.loads(pin(boundary.parent/'deltas.json').read_bytes())['tree_composed']):
  assert inverse.count(d['new'])==1;inverse=inverse.replace(d['new'],d['old'])
 assert inverse==pin(R/'tools/m4-startup138-original/tree_source_r5.py').read_text(encoding='utf-8')
 validation=pin(R/'reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c');strict=json.loads(validation.read_bytes());assert strict['passed']and strict['reader_closed']and strict['paired_export_readers_closed']and strict['callbacks']==111
 retained_canonical=[]
 for f,h in strict['files'].items():
  q=Path(f)
  if q.drive.upper()=='G:'or q.suffix.lower()in('.mwb','.mwi')or q.name=='transport.json':retained_canonical.append(dict(path=f,sha256=h,read=False));continue
  pin(q,h)
 rows=strict['paired_exports'];assert len(rows)==1 and rows[0]['branch']=='original';row=rows[0];assert row['logical_files']==261543 and row['payload_bytes']==1540126431 and row['transport_sha256']=='31434a1b433b4340e4d11daa45c48bf3bdfaa3ea6a930a83af5589650e2827ff'
 pin(row['index_path'],'ed0cc1d43b26c067f0af85dd153f5ce5fd38ae07f789d893bcbad812b97c13ae');pin(row['payload_path'],'8a23f0a6be87e38ff50f9591f57988fa5e87850e4429655a2357aa98f599331b')
 assert row['index_sha256']==files[str(Path(row['index_path']).resolve())]and row['payload_sha256']==files[str(Path(row['payload_path']).resolve())]
 driver=pin(R/'tools/m4-original141-tree-source/run_ordinary_v2.py');ast.parse(driver.read_text(encoding='utf-8'));pin(__file__)
 admission=R/'reports/m4-original141-tree-source/root-source-admission-r1/report.json'
 recipe=dict(required_ROOT_final_fields=dict(passed=True,original141_tree_source_admitted=True,validation_sha256=sha(validation),preparation_sha256=sha(prep)),required_independent_reviews=['whole15 finite child inverse plus one runner binding and all13 ordinary-only pin controls','current selected141 removing exact3 roots equals whole138 order','all18 production phase/shim/current-export controls','all actual source/model/contract files physically rehashed before ordinary reader','current ROOTcompiled2 whole links and actual named two Lockit shims','current strict3 ordinary export entire index and payload hashes'],command=[sys.executable,'-B',str(driver),str(validation),sha(validation),str(prep),sha(prep),str(admission),'<ROOT_FINAL_ADMISSION_SHA256>','source-r1'],source_case_extent=6,root=0x4b7f70,phase=86,expected_finite_counts=dict(whole_original_FS_records=126,whole_original_CPU_FX_ENV_frame_CS_boundaries=468,bounded_original_API_volatile_inputs=156,actual_initial_allocator_witnesses=42,whole_original_nonstack_pages=408,whole_original_owner_backings=42),typed_source_scope='Literal tree prefix/owner byteflow and typed API scalar/CS24 frontier; full original State/provider stack/postRET observation remain unclaimed',no_canonical_reader=True,no_worker=True,strict_export_row=row)
 p=out/'recipe.json';p.write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf-8');pin(p)
 p=out/'canonical-provenance-not-opened.json';p.write_text(json.dumps(retained_canonical,indent=2)+'\n',encoding='utf-8');pin(p)
 union=out/'current-ordinary-input-union.json';union.write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');pin(union)
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,prepared_only=True,original141_tree_source_admitted=False,ROOT_admission_required=True,validation_sha256=sha(validation),preparation_sha256=sha(prep),exact_fifteen_delta_inverse=True,entire_ordinary_export_index_payload_rehashed=True,ordinary_source_reader_opened=False,canonical_reader_opened=False,worker_launched=False,initializer_credit=0,accepted_function_credit=0,files=files),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(p),union_sha256=sha(union),inputs=len(files))))
if __name__=='__main__':main()

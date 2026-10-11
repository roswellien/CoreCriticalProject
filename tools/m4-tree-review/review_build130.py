"""Independent final130 ABI/link/resource source and measured output review; no captures."""
from pathlib import Path
import json,hashlib,re,sys,struct
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();d=sha(p);assert h is None or d==h,(p,h,d);P[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
 area=R/'reports/m4-startup130-build-review';digests={'abi-r2':'8c6b90b32459c7522f6a6d00154504bb2c46f492b24927348f93c8c2bfa3c1bc','link-r3':'087d064d433bf16e77c1de3416414b265cdd36435cd8277d7042fa05d4eec86c','resource-r3':'9a1329d6e790789e765971062d976cda70006d015e6f212ae9658d6aa37f1c93'}
 reports={n:read(area/n/'report.json',h)for n,h in digests.items()};abi,link,res=(reports[x]for x in digests)
 for gate in reports.values():
  assert gate['passed']and gate['bound_final_build_sha256']=='1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53'
  for p,h in gate['files'].items():assert Path(p).suffix not in('.mwb','.zip');pin(p,h)
 assert abi['packed_schema_identical_to_accepted125']and(abi['unique_whole_pages'],abi['selected_roots'],abi['registrations'])==(46,130,101)
 for level in abi['levels']:
  v=level['values'];assert v['pointer_bytes']==8 and(v['State'],v['Cpu'],v['Native'])==(3504,40,159716)and v['CPU_after']==[76,116]and v['FX_before']==[116,628]and(v['fixed_pages'],v['external_pages'])==(17,29)
  args=level['command'];assert '/machine:x64'in args and '/clang:-frounding-math'in args and '/DADDRESS_SIZE_BITS=32'in args
 assert link['literal_COFF_links']==794 and link['compiled_objects']==60 and link['actual_linked_inputs']==858
 for level in link['levels']:assert(level['literal_COFFs'],level['added_literal_COFFs'],level['compiled_objects'],level['canonical_capture_objects'],level['actual_linked_inputs'],level['retained_unlinked_archives'])==(397,26,30,2,429,1)
 symbols=link['new_literal_symbols'];assert len(symbols)==52
 for level in('O0','O2'):
  rows=[r for r in symbols if r['level']==level];assert len(rows)==26
  cos=[r for r in rows if any('sub_4b64f0'in x for x in r['defined_external_symbols'])];assert len(cos)==1
  defined={x.split()[-1]for x in cos[0]['defined_external_symbols']if x.split()[1]=='T'}
  assert defined=={'mw34_fp_entry_4b64f0','sub_4b64f0','mw34_compound___remill_flag_computation_sign','mw34_compound___remill_flag_computation_zero','mw34_compound___remill_undefined_8'}
  assert all(sum('_body'in x for x in r['defined_external_symbols'])==1 for r in rows if r!=cos[0])
 assert res['guest_CS_bytes']==24 and res['native_resource_bytes']==40 and res['guest_semantic_DWORD_offsets']==[4,8,12]and res['opaque_loaded_DWORD_offsets']==[0,16,20]and not res['seeded_state2']
 for level in res['levels']:assert level['actual_defined_resource_methods']==26 and len(level['compiler_consumed_source_dependencies'])==12
 for row in res['loaded_pages']:assert len(pin(row['path'],row['sha256']).read_bytes())==row['bytes']==4096
 actual_wrapper=pin(R/'tools/m4-startup130-build-review/build_abi_v3.ps1').read_text();assert "'review_v3.py') abi $Output"in actual_wrapper and '-arch=x64 -host_arch=x64'in actual_wrapper
 actual=pin(R/'tools/m4-startup130-build-review/review_v3.py').read_text();assert 'checks.PREPSHA = \'060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c\''in actual and 'result[2](parent)'in actual and 'checks.__file__'in actual
 body=pin(R/'tools/m4-startup130-build-review/review.py').read_text()
 for required in("assert len(compiled)==30 and len(linked)==429","linked-literal==set(compiled.values())", "Path(archive).name not in graph", "assert selected==[x['entry']for x in p['selected_order']]", "assert values['Native']==159716 and values['CPU_after']==[76,116] and values['FX_before']==[116,628]", "pin(s,sources[s]);pin(o,declared[o])"):assert required in body,required
 resource=pin(R/'tools/m4-startup130-build-review/resource_v3.py').read_text();assert "text.replace('from review import', 'from review_v3 import')"in resource and "m4-startup130-build-review/resource_v2.py"in resource
 contracts=read(R/'reports/m4-tree-review/cleanup19-r2/report.json','ba43095f791a7e16d2e747e2c1f3d414e15d29744588b91509fb1ee7122b4afb');assert contracts['passed']
 preflight=read(R/'reports/m4-tree-review/joint130-prelaunch-r4/report.json','07160a265d87dbca459b77f34bf1242f73bcd1743b5396cbf419084424d252fe');assert preflight['passed']and preflight['build_sha256']==link['build_sha256']
 pin(__file__);target=out/'report.json';target.write_text(json.dumps(dict(passed=True,scope='Independent physically pinned current130 AMD64 compiler ABI, complete429-input-per-level link graph, exact symbols/resource methods and executed wrapper code closure; no archive or semantic execution substitute',bound_final_build_sha256=link['build_sha256'],native_preparation_sha256=link['native_preparation_sha256'],ABI_sha256=digests['abi-r2'],link_sha256=digests['link-r3'],resource_sha256=digests['resource-r3'],actual_ABI_levels=2,literal_COFF_links=794,compiled_objects=60,actual_linked_inputs=858,resource_defined_methods_per_level=26,known_literal_body_objects_per_level=25,compound_exact_external_symbols_per_level=5,whole_bootstrap_pages=2,capture_archives_opened=0,all_final_machine_body_attribution_claim=False,initializer_credit=0,files=P),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(target),physical_files=len(P))))
if __name__=='__main__':main(sys.argv[1])

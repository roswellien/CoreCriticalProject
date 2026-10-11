"""Compact map of completed120 source gates; no root admission or recount."""
from pathlib import Path
import collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-next-source'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=BASE/name
 assert not out.exists(),'Fresh compact source receipt map'
 roles={
 'source_recovery':'reports/m4-next-source/recovery-r1/report.json',
 'game_lifts':'reports/m4-next-source/lifts-r1/report.json',
 'game_symbols':'reports/m4-next-source/symbol-attribution-r2/report.json',
 'game_callbacks':'reports/m4-next-source/game-callbacks-r1/report.json',
 'geometry':'reports/m4-container-source/geometry-r2/report.json',
 'allocation_interface':'reports/m4-container-source/allocation-interface-r1/report.json',
 'loader_identity':'reports/m4-container-source/loader-identity-r2/report.json',
 'provider_lifts':'reports/m4-container-source/provider-lifts-r1/report.json',
 'original_prepare':'reports/m4-vtable-original/preparation-r3/report.json',
 'original_build':'reports/m4-vtable-original/build-r2/build.json',
 'original_execution':'reports/m4-vtable-original/execution-r1/report.json',
 'original_validation':'reports/m4-vtable-original/validation-r1/report.json',
 'original_source':'reports/m4-next-source/original-game-source-r1/report.json',
 'original_FS':'reports/m4-next-source/original-FS-observations-r1/report.json',
 'source':'reports/m4-next-source/connected-native-source-r2/report.json',
 'paired':'reports/m4-next-source/paired-policy-r1/report.json',
 'paired_FS':'reports/m4-next-source/paired-FS-normal-policy-r1/report.json',
 'paired_owned':'reports/m4-next-source/paired-owned-policy-r1/report.json',
 'indirect_interface':'reports/m4-next-source/indirect-interface-r2/report.json',
 'indirect_source':'reports/m4-next-source/indirect-source-r1/report.json',
 }
 inherited={'geometry','allocation_interface','loader_identity','provider_lifts'}
 pins={};result={}
 for role,name in roles.items():
  p=ROOT/name;r=json.loads(p.read_bytes());assert r['passed'],(role,'Only passed current gates')
  h=sha(p);pins[str(p.resolve())]=h
  result[role]=dict(path=name,sha256=h,counts=r.get('counts',{}),inherited_from_accepted116=role in inherited)
  result[role]['source_scope_flags']={k:v for k,v in r.items()if isinstance(v,bool)}
 parent=ROOT/'reports/m4-joint-startup116-root/acceptance-r1/report.json'
 assert sha(parent)=='de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6'
 pins[str(parent.resolve())]=sha(parent);pins[str(Path(__file__).resolve())]=sha(__file__)
 out.mkdir()
 report=dict(passed=True,scope='Compact identity map of completed immutable120 original, native, paired, normal FS and finite indirect evidence; provider/control audit and root admission remain separate. Four new roots reuse accepted116 allocation/provider/loader geometry with zero new owner or API operations.',roles=result,selected_roots=120,new_roots=4,new_provider_or_owner_operations=0,AFTER_machine_seed=False,handler_execution=False,nonzero_pointer_path=False,callback_execution=False,whole_M4_complete=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),roles={k:dict(path=v['path'],sha256=v['sha256'],counts=v['counts'])for k,v in result.items()})))
if __name__=='__main__':main(sys.argv[1])

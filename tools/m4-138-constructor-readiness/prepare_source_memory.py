"""Fresh source/helper derivative for physical PE ownership only."""
from pathlib import Path
import ast,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-joint-startup138-source'/name;assert not out.exists();pins={};deltas=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,str(p);pins[str(p)]=v;return p
 failure=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r2/report.json','5d3ba04c95518434e0e1884ced262936fcd9c6d8b9155c605c00acffc7787a51');f=json.loads(failure.read_bytes());assert not f['passed']and f['reader_closed']and f['paired_export_readers_closed']
 parent=R/'reports/m4-joint-startup138-source/preparation-r4';d=json.loads(pin(parent/'report.json').read_bytes());assert d['passed']
 helper_parent=pin(R/'tools/m4-joint-startup138/persistent_widgets_v2.py',d['files'][str((R/'tools/m4-joint-startup138/persistent_widgets_v2.py').resolve())]);helper=R/'tools/m4-joint-startup138/persistent_widgets_v5.py';assert not helper.exists()
 ht=helper_parent.read_text();insert='''
import importlib.util
_game_spec=importlib.util.spec_from_file_location('current138_game_owned_memory',ROOT/'tools/m4-138-constructor-readiness/mapped_game_memory_v2.py')
GAME_OWNERSHIP=importlib.util.module_from_spec(_game_spec);_game_spec.loader.exec_module(GAME_OWNERSHIP)
admit_game_regions=GAME_OWNERSHIP.admit
'''
 a='ROOT = Path(__file__).resolve().parents[2]';assert ht.count(a)==1;ht=ht.replace(a,a+insert,1)
 a='    regions=[]\n    for name in names:';b='''    regions=[]
    need(hasattr(machine,'_source_game_ownership'),'Source-owned PE allocations admitted before bootstrap')
    actual_inventory=[(int(name[len(prefix+'game-region-'):-4]),len(archive.data(name)))for name in names]
    equal(sorted(actual_inventory),machine._source_game_ownership['regions'],'Every and only independently PE-owned Game region')
    for name in names:''';assert ht.count(a)==1;ht=ht.replace(a,b,1);ast.parse(ht);helper.write_text(ht);pin(helper)
 for p in parent.iterdir():
  if p.is_file()and p.name not in('report.json','compare_provider138.py'):pin(p,d['files'][str(p.resolve())])
 out.mkdir(parents=True)
 for p in parent.iterdir():
  if p.is_file()and p.name not in('report.json','compare_provider138.py'):shutil.copyfile(p,out/p.name);pin(out/p.name)
 cp=pin(parent/'compare_provider138.py',d['files'][str((parent/'compare_provider138.py').resolve())]);t=cp.read_text()
 for a,b in [('persistent_widgets_v2.py','persistent_widgets_v5.py'),
  ('super().__init__(*args,**kwargs);self._source_undefined_flags={};self._source_flag_consumers=[]',
   'super().__init__(*args,**kwargs);self._source_game_ownership=PW.admit_game_regions(self,pe);self._source_undefined_flags={};self._source_flag_consumers=[]'),
  ('machine,responses=B2.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp,resource_association=resource_association)',
   "machine,responses=B2.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp,resource_association=resource_association);loader_rows.append(dict(level=level,sequence=seq,source_PE_ownership=machine._source_game_ownership))"),
  ('pin(PW.__file__);pin(PG.__file__);','pin(PW.__file__);pin(PW.GAME_OWNERSHIP.__file__);pin(PG.__file__);')]:
  assert t.count(a)==1,a;t=t.replace(a,b,1);deltas.append(dict(before=a,after=b))
 ast.parse(t);target=out/'compare_provider138.py';target.write_text(t);pin(target)
 for p in [R/'tools/m4-138-constructor-readiness/mapped_game_memory_v2.py',R/'tools/m4-startup/image_loader.cpp',R/'tools/analysis/pe.py',R/'MW3/Mech3.exe',Path(__file__),Path(sys.executable)]:pin(p)
 report=dict(passed=True,scope='Unexecuted carried138 source ownership extension from physical own PE loader before bootstrap; original checkpoint whole-byte/equality and all prior semantic gates retained',
  entrypoint=str(target),helper=str(helper),helper_sha256=sha(helper),parent_preparation_sha256=sha(parent/'report.json'),failure_sha256=sha(failure),
  comparator_deltas=deltas,source_roots=138,source_cases=12,source_phases=1656,
  initializer_credit=0,capture_archive_reader_opened=False,source_execution_performed=False,AFTER_State_or_memory_seed=False,
  existing_source_bytes_preserved=True,all_Game_region_bytes_still_compared=True,allocation_inventory_derived_from_physical_PE=True,
  independent_review_required_before_rerun=True,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),comparator_sha256=sha(target),helper_sha256=sha(helper))))
if __name__=='__main__':main(sys.argv[1])

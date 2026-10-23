"""Cold actual metadata/import read inventory; never creates a source machine."""
from pathlib import Path
import hashlib,importlib.util,json,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/import-inventory-r2';out.mkdir();seen=set();active=True
 def audit(event,args):
  if not active or event!='open':return
  value,mode,flags=args
  if not isinstance(value,(str,bytes,Path)):return
  p=Path(value.decode()if isinstance(value,bytes)else value).resolve()
  if p.suffix.lower()=='.pyc':raise FileNotFoundError('Use actual Python source')
  assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'and p.drive.upper()!='G:','No capture or payload inputs in static inventory'
  assert not((isinstance(mode,str)and any(c in mode for c in('w','a','x','+')))or(isinstance(flags,int)and flags&(1|2|64|512|1024))),'No writes during static model metadata inventory'
  seen.add(p)
 sys.addaudithook(audit)
 def load(p,n):
  sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
 try:
  tree=load(R/'tools/m4-tree-source/game_model_v4.py','tree141_static_model');program,callbacks=tree.source_program();contract=tree.contract()
  projection=load(R/'tools/m4-joint-startup27-review/observe.py','tree141_static_projection');models=projection.models()
  load(R/'tools/m4-mfc-source/compare_original_game.py','tree141_static_state');load(R/'tools/analysis/pe.py','tree141_static_PE');load(R/'tools/m4-crt-allocation-root/run_v2.py','tree141_static_unused_parent_import');load(R/'tools/m4-startup138-original/registry_suffix_v1.py','tree141_static_suffix');load(R/'tools/m4-startup131-original/export_reader.py','tree141_static_export')
  assert 0x4b7f70 in program and {r['CALL_pc']for r in contract['allocations']}=={0x4ba306,0x4ba33c,0x4bab32}
 finally:active=False
 for module in list(sys.modules.values()):
  filename=getattr(module,'__file__',None)
  if filename and Path(filename).is_file()and Path(filename).suffix.lower()not in('.pyc','.zip'):seen.add(Path(filename).resolve())
 seen.add(Path(__file__).resolve());files={}
 for p in seen:
  if not p.exists():continue
  with p.open('rb')as f:files[str(p)]=hashlib.file_digest(f,'sha256').hexdigest()
 report=dict(passed=True,prepared_only=True,source_program_rows=len(program),callback_rows=len(callbacks),actual_cold_import_and_metadata_reads=len(seen),source_machine_constructed=False,source_machine_executed=False,ordinary_reader_opened=False,canonical_reader_opened=False,worker_launched=False,all_cache_reads_refused=True,files=files);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()

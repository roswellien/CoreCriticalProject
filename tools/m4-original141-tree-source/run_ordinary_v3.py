"""Six genuine original141 tree cases from one sealed ordinary export reader."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(validation_path,validation_sha,preparation_path,preparation_sha,admission_path,admission_sha,name):
 validation_path=Path(validation_path).resolve();preparation_path=Path(preparation_path).resolve();admission_path=Path(admission_path).resolve();out=R/'reports/m4-original141-tree-source'/name;assert not out.exists();out.mkdir(parents=True);pins={};reader=None;cases=[];counts=collections.Counter();passed=False;authorized=None;audit_active=False;audit_inside=False;produced=set()
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in ('.mwb','.mwi','.zip')and p.name!='transport.json','No canonical reader or transport access';assert authorized is None or str(p)in authorized or str(p)in produced,'Every actual external source input belongs to ROOT admission before open';v=sha(p);assert authorized is None or str(p)in produced or v==authorized[str(p)],'Actual source input matches admitted physical identity';assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  sp=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
 try:
  gate=read(admission_path,admission_sha);assert gate['passed']and gate['original141_tree_source_admitted']is True;assert gate['validation_sha256']==validation_sha and gate['preparation_sha256']==preparation_sha
  authorized=dict(gate['files']);authorized[str(admission_path)]=admission_sha
  def audit(event,args):
   nonlocal audit_inside
   if event!='open'or audit_inside:return
   value,mode,flags=args
   if not isinstance(value,(str,bytes,Path)):return
   path=Path(value.decode()if isinstance(value,bytes)else value).resolve();key=str(path)
   writing=(isinstance(mode,str)and any(c in mode for c in('w','a','x','+')))or (isinstance(flags,int)and bool(flags&(1|2|64|512|1024)))
   own=(path.is_relative_to(out)or (path.parent.parent==out.parent and path.parent.name.startswith(name+'-case-')and path.parent.name[len(name+'-case-'):].isdigit()and 0<=int(path.parent.name[len(name+'-case-'):])<6))
   if writing:
    assert own,'Source output must remain in exact fresh aggregate/sixcase namespace';produced.add(key);return
   if key in produced:return
   # Refuse stale bytecode; import machinery must compile the admitted Python source.
   if path.suffix.lower()=='.pyc':raise FileNotFoundError('Admitted source required, cached bytecode refused')
   assert key in authorized,'Direct source/import read is absent from ROOT admission: '+key
   assert path.suffix.lower()not in('.mwb','.mwi','.zip')and path.name!='transport.json','No direct canonical capture access'
   audit_inside=True
   try:assert sha(path)==authorized[key],'Direct source read exact physical admission: '+key
   finally:audit_inside=False
  sys.addaudithook(audit);audit_active=True

  assert gate['files'][str(Path(__file__).resolve())]==sha(__file__)
  for p,h in gate['files'].items():pin(p,h)
  prepared=read(preparation_path,preparation_sha);assert prepared['passed']and prepared['prepared_only']
  for p,h in prepared['files'].items():pin(p,h)
  validation=read(validation_path,validation_sha);assert validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']and validation['callbacks']==111
  for p,h in validation['files'].items():
   q=Path(p)
   # Canonical capture files are not reopened; the sealed ordinary export owns its own hashes.
   if q.drive.upper()=='G:' or q.suffix.lower()in('.mwb','.mwi')or q.name=='transport.json':continue
   pin(q,h)
  E=load(R/'tools/m4-startup131-original/export_reader.py','tree141_ordinary_export');T=load(R/'tools/m4-original141-tree-source/tree_source_v3.py','tree141_source');T.PINS=pins;T.pin=pin
  reader=E.ExportReader(validation_path,validation_sha,'original',pin);T.SHARED_READER=reader
  for sequence in range(6):
   childname=name+'-case-'+str(sequence);T.main(childname,R/'tools/m4-tree-source/game_model_v4.py',sequence,validation_path,validation_sha);p=R/'reports/m4-original141-tree-source'/childname/'report.json';child=read(p);assert child['passed']and child['sequence']==sequence and child['original_validation_sha256']==validation_sha and child['source_AFTER_seed']is False;assert child['all_current_frame_source_written_bytes_compared']and child['opaque_disagreements_proven_unused_before_overwrite']and child['original_unused_frame_bytes_seeded']is False
   for f,h in child['files'].items():pin(f,h)
   derived=read(p.parent/'source-derivations.json',child['files'][str((p.parent/'source-derivations.json').resolve())]);assert derived['phase']==86;cases.append(dict(sequence=sequence,path=str(p),sha256=sha(p),source=derived));counts.update(child['counts'])
  assert len(cases)==6 and counts['whole_original_owner_backings']==42 and counts['actual_initial_allocator_witnesses']==42
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
 finally:
  if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()
  for p,h in pins.items():assert sha(p)==h
  p=out/'original-Tree-source-derivations.json';p.write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8');pin(p)
  report=dict(passed=passed,original_validation_path=str(validation_path),original_validation_sha256=validation_sha,source_case_extent=len(cases),source_AFTER_seed=False,canonical_reader_opened=False,ordinary_reader_closed=True,all_external_inputs_admitted_before_open=audit_active,direct_source_import_reads_audited=audit_active,counts=dict(counts),source_instruction_model_unchanged=True,tree_phase=86,whole_original_State_claim=False,whole_provider_stack_compared=False,original_postRET_observed=False,original_postRET_source_derived=True,all_current_frame_source_written_bytes_compared=passed,opaque_disagreements_proven_unused_before_overwrite=passed,initializer_credit=0,accepted_function_credit=0,files=pins)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=passed,report_sha256=sha(p),cases=len(cases))))
if __name__=='__main__':main(*sys.argv[1:])

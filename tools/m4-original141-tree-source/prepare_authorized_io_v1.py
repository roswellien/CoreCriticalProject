"""Finite aggregate pin admission and audited direct source input reads."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/authorized-io-preparation-r1';out.mkdir();files={};deltas=[]
 def pin(p):
  p=Path(p).resolve();files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
 parent=pin(R/'tools/m4-original141-tree-source/run_ordinary_v2.py');s=parent.read_text(encoding='utf-8')
 def edit(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);deltas.append(dict(old=a,new=b))
 edit("pins={};reader=None;cases=[];counts=collections.Counter();passed=False", "pins={};reader=None;cases=[];counts=collections.Counter();passed=False;authorized=None;audit_active=False;audit_inside=False;produced=set()")
 edit("p=Path(p).resolve();assert p.suffix.lower()not in ('.mwb','.mwi','.zip')and p.name!='transport.json','No canonical reader or transport access';v=sha(p);assert h is None or h==v;", "p=Path(p).resolve();assert p.suffix.lower()not in ('.mwb','.mwi','.zip')and p.name!='transport.json','No canonical reader or transport access';assert authorized is None or str(p)in authorized or str(p)in produced,'Every actual external source input belongs to ROOT admission before open';v=sha(p);assert authorized is None or str(p)in produced or v==authorized[str(p)],'Actual source input matches admitted physical identity';assert h is None or h==v;")
 anchor="gate=read(admission_path,admission_sha);assert gate['passed']and gate['original141_tree_source_admitted']is True;assert gate['validation_sha256']==validation_sha and gate['preparation_sha256']==preparation_sha"
 addition=anchor+"""
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
"""
 edit(anchor,addition)
 edit("T.PINS=pins", "T.PINS=pins;T.pin=pin")
 edit("ordinary_reader_closed=True,counts=", "ordinary_reader_closed=True,all_external_inputs_admitted_before_open=audit_active,direct_source_import_reads_audited=audit_active,counts=")
 reverse=s
 for d in reversed(deltas):assert reverse.count(d['new'])==1;reverse=reverse.replace(d['new'],d['old'])
 assert reverse==parent.read_text(encoding='utf-8');ast.parse(s);q=parent.with_name('run_ordinary_v3.py');assert not q.exists();q.write_text(s,encoding='utf-8');pin(q);pin(__file__)
 p=out/'deltas.json';p.write_text(json.dumps(deltas,indent=2)+'\n',encoding='utf-8');pin(p)
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,prepared_only=True,exact_five_runner_delta_inverse=True,external_input_membership_before_open=True,source_child_pin_delegated=True,direct_import_source_reads_audit_required=True,bytecode_not_admitted=True,new_outputs_only_aggregate_and_exact_six_case_dirs=True,canonical_reader_opened=False,ordinary_reader_opened=False,worker_launched=False,files=files),indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()

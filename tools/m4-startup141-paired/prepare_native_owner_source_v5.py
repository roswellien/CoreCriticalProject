"""Prepare own-source v5 exact supplement/adaptor bindings; no imports/readers."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-constructor-source-preparation-r5';assert not out.exists();out.mkdir();p=R/'tools/m4-startup141-paired/constructor_native36_source141_v4.py';q=p.with_name('constructor_native36_source141_v5.py');assert not q.exists();a=p.read_text();b=a;edits=[]
 def edit(x,y):
  nonlocal b
  assert b.count(x)==1;b=b.replace(x,y);edits.append((x,y))
 edit('def main(admission_path,admission_sha,configuration_path,configuration_sha,name):','def main(admission_path,admission_sha,configuration_path,configuration_sha,owner_export_path,owner_export_sha,name):')
 edit("admitted[str(admission_path)]=admission_sha","admitted[str(admission_path)]=admission_sha\n assert admission['owner_export_sha256']==owner_export_sha")
 edit('passed=False;f=None;cases=[]','passed=False;f=None;owner_reader=None;cases=[]')
 edit("constructor_native_input141_v2.py","constructor_native_input141_v3.py")
 edit("  for level in('O0','O2'):","""  supplement=json.loads(pin(owner_export_path,owner_export_sha).read_bytes());need(supplement['passed']and supplement['reader_closed']and supplement['paired_export_readers_closed']and supplement['model_executed']is False and supplement['worker_launched']is False and supplement['source_sha256']==C['native_source']['sha256']and supplement['execution_sha256']=='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6','Exact closed ROOT-admitted current owner-cut export, not source credit')
  need(len(supplement['cases'])==36 and {(v['level'],v['sequence'],v['root'])for v in supplement['cases']}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in(0x4103f0,0x410440,0x459b40)},'Complete distinct current owner-cut36')
  for level in('O0','O2'):
   owner_reader=E.ExportReader(owner_export_path,owner_export_sha,level,pin)""")
 edit('inp=A.build(f,level,seq,root,carried);write',"""cut=next(v for v in supplement['cases']if(v['level'],v['sequence'],v['root'])==(level,seq,root));need(cut['checkpoint_name']=='constructor-mfc-before'and cut['static_or_stack_checkpoint_bytes_seeded']is False,'Only typed own dynamic-owner input cut')
     owner_cut=dict(level=level,sequence=seq,root=root,checkpoint_prefix=cut['checkpoint_prefix'],checkpoint_name=owner_reader.data(cut['checkpoint_prefix']+'-name.bin').decode(),pages=[dict(address=int(k.rsplit('-page-',1)[1][:-4]),logical_key=k,bytes=owner_reader.entries[k]['bytes'],sha256=owner_reader.entries[k]['sha256'],hex=owner_reader.data(k).hex())for k in cut['keys']['owner_input']]);inp=A.build(f,level,seq,root,carried,owner_cut);write""")
 edit('     owner_count=0',"""     # Terminal owner bytes are opened only after literal execution and never
     # enter the BEFORE adapter or source response model.
     need(owner_reader.data(cut['endpoint_checkpoint_prefix']+'-name.bin')==b'widget-onexit-after','Exact current terminal registrar owner equality cut')
     for key in cut['keys']['endpoint']:
      address=int(key.rsplit('-page-',1)[1][:-4]);need(0x31000000<=address<0x32000000 and address not in memory,'Distinct current full terminal dynamic owner target');memory[address]=owner_reader.data(key)
     owner_count=0""")
 edit('   f.close();f=None','   f.close();f=None;owner_reader.close();owner_reader=None')
 edit('  if f is not None:f.close()','  if f is not None:f.close()\n  if owner_reader is not None:owner_reader.close()')
 edit('current_original18_sha256=C[', 'owner_export_sha256=owner_export_sha,current_original18_sha256=C[')
 ast.parse(b);q.write_text(b);back=b
 for x,y in reversed(edits):assert back.count(y)==1;back=back.replace(y,x)
 assert back==a;delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a.splitlines(True)[i:j]),child=''.join(b.splitlines(True)[k:l])))
 inv=out/'inverse.json';inv.write_text(json.dumps(delta,indent=2)+'\n');paths=[p,q,inv,R/'tools/m4-startup141-paired/constructor_native_input141_v3.py',R/'reports/m4-startup141-paired/native-owner-cut-preparation-r1/report.json',R/'reports/m4-startup141-paired/native-owner-export-preparation-r2/report.json',Path(__file__).resolve()];r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,reader_opened=False,source_execution=False,root_admission_minted=False,source_main=str(q),whole_parent_inverse=True,inverse_hunks=len(delta),before_owner_cut_only=True,terminal_owner_targets_opened_after_source=True,previous_nonphase_full_region_carry_proven=False,actual_supplement_and_source_execution_pending=True,CLI='Python -B SOURCE ROOT_ADMISSION SHA CONFIG SHA OWNER_EXPORT SHA FRESH_NAME',files={str(v.resolve()):sha(v)for v in paths}),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),source_sha256=sha(q))))
if __name__=='__main__':main()

"""Additive source observer for the109 persistent game/provider corpus."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(name):
 out=ROOT/'reports/m4-fs-provider-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};generated={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def write(p,s):
  assert not p.exists();ast.parse(s,filename=str(p));p.write_text(s,encoding='utf-8');generated[str(p.resolve())]=sha(p)
 parent=pin(ROOT/'tools/m4-mfc-review/final_observer.py');s=parent.read_text()
 a="  self.specs=json.loads(self.pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json').read_bytes())"
 s=one(s,a,a+"\n  self.fs_specs=json.loads(self.pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes())\n  self.specs+=self.fs_specs\n  accesses=json.loads(self.pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/shared-owner-accesses.json').read_bytes())\n  self.fs_allowed={(r['root'],r['pc'],r['bytes'],r['owner_root'],r['owner_CALL_pc'],r['owner_offset'],r['write'])for r in accesses}")
 start=s.index("  if event=='write-after'and data['domain']=='source':");end=s.index("  if event=='returned'and data['caller']:",start)
 s=s[:start]+'''  if event=='write-after'and data['domain']=='source':
   pc=data['pc'];address=data['address'];size=data['bytes'];value=data['value'];record=None;kind=0
   for candidate in self.mfc:
    w=candidate['words']
    if w[16]and w[16]<=address and address+size<=w[16]+w[7]:record=candidate;kind=1;break
    if candidate['spec']not in self.fs_specs and w[2]==self.root and w[21]and size==4 and value==w[16]and address==candidate['spec']['publication']:record=candidate;kind=2;break
   if record:
    w=record['words']
    if w[2]!=self.root:
     need((self.root,pc,size,w[2],w[4],address-w[16],True)in self.fs_allowed,'Exact literal cross-root source owner/PC/requested offset')
     COUNTS['exact_FS_prior_owner_source_stores']+=1
    self.mfc_stores.append((1,w[1],w[2],pc,address,size,value,kind));w[24]+=size if kind==1 else 0;w[23]+=int(kind==2)
   if size==4:
    for spec in self.fs_specs:
     if spec['root']!=self.root or spec['publication_PC']!=pc:continue
     candidate=next((r for r in self.mfc if r['words'][2]==spec['root']and r['words'][4]==spec['CALL_pc']),None)
     if not candidate or candidate['words'][16]!=value:continue
     w=candidate['words'];expected=spec['publication'];parent=spec['publication_owner']
     if parent:
      earlier=next(r for r in self.mfc if r['words'][2]==parent['root']and r['words'][4]==parent['CALL_pc']);expected=earlier['words'][16]+parent['offset']
     need(address==expected and w[23]==0,'Source-established dynamic/static FS publication and exact earlier owner')
     w[23]+=1;COUNTS['exact_FS_primary_publications']+=1
''' +s[end:]
 replacements=[("len(actual)==len(self.mfc)==35","len(actual)==len(self.mfc)==45"),("Exact35 source allocation calls across32 initializer roots","Exact45 source allocation calls across38 MFC initializer roots"),("len(allocations)==len(responses.allocations)==52","len(allocations)==len(responses.allocations)==62"),("One real producer,16 strings and35 actual MFC private owners","One real producer,16 strings and45 actual MFC private owners"),("sum(a.get('kind',1)==4 for a in responses.allocations)==35","sum(a.get('kind',1)==4 for a in responses.allocations)==45"),("registry-replay-{75+n}","registry-replay-{81+n}"),("complete103_provider_sequences","complete109_provider_sequences"),("selected_registration_closures']+=75","selected_registration_closures']+=81"),("actual_MFC_allocations']+=35","actual_MFC_allocations']+=45"),("actual_source_frees']+=52","actual_source_frees']+=62"),("actual_MFC_source_frees']+=35","actual_MFC_source_frees']+=45"),("actual_MFC_allocations=35","actual_MFC_allocations=45")]
 for a,b in replacements:
  assert a in s,a;s=s.replace(a,b)
 write(HERE/'final_observer109.py',s)
 source=pin(ROOT/'tools/m4-mfc-review/observe_connected.py');s=source.read_text();s=one(s,'import final_observer as V','import final_observer109 as V')
 s=s.replace("ROOT/'reports/m4-mfc-review'/name","ROOT/'reports/m4-fs-provider-review'/name")
 s=s.replace("ROOT/'tools/m4-mfc-source/game_model.py'","ROOT/'tools/m4-fs-source/game_model.py'")
 s=one(s,"op=pin(ROOT/'reports/m4-mfc-source/original-run-r3/report.json','a50819520282272712899cb64faedd8d568c08a22d6d25e65fbc18358571faa0')","op=pin(ROOT/'reports/m4-fs-source/original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4')")
 a="+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes());roots=";b="+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots=";s=one(s,a,b)
 s=one(s,"order=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json').read_bytes())['selected_order']","order=json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==109,'Exact full109 source order')")
 s=s.replace('103','109').replace("len(expected_callbacks)==75","len(expected_callbacks)==81").replace('All75 actual callback','All81 actual callback')
 s=s.replace("Path(__file__).with_name('final_observer.py')","Path(__file__).with_name('final_observer109.py')")
 write(HERE/'observe109.py',s)
 pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/report.json','f7440d694771cc39c662a9842f7673c0c97d63274505b41894e325bcfde48a9b');pin(ROOT/'tools/m4-fs-source/game_model.py');pin(__file__)
 r=dict(passed=True,scope='Additive independent persistent109 source/provider observation tool preparation; original instruction models and actual typed API leaves reused unchanged',new_observer_sources=generated,source_inputs=pins,provider_API_result_injection=False,per_phase_reseed=False,native_executed=False,initializer_credit=False)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),tools=2)))
if __name__=='__main__':main(sys.argv[1])

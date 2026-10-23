"""Exact current13 compiled CRT observer transitions; dynamic named targets remain typed-input gate."""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141/root-transition-controls-r1';files={};checks=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 base=R/'reports/m4-original141/source-preparation-r6';build=R/'reports/m4-original141/build-r2';release=build/'build-x86/mw34_joint_startup124_original.dir/Release'
 proof=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/report.json','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c').read_bytes());assert proof['passed'];links=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json').read_bytes());old=json.loads(pin(R/'reports/m4-138-validation-review/mfc-transition-r3/patch-identities.json').read_bytes());res={}
 required={r['symbol']for r in old}
 for row in links:
  for rel in row['relocations']:
   name=rel['symbol']
   if name in required and rel['resolution_kind']=='virtual address':assert name not in res or res[name]==rel['actual_symbol_address'];res[name]=rel['actual_symbol_address']
 C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','CRT_transition_coff')
 for family in('reference_x86','fs_observer_x86','nullfree_observer_x86'):
  symbols,sections=C.coff(pin(release/(family+'.obj')).read_bytes());whole=next(x for x in links if x['symbol']==family+' whole source');sec=[n for n,s in sections.items()if s['flags']&0x20000000 and s['bytes']];assert len(sec)==1;section=sec[0];assert sections[section]['bytes'].hex()==whole['object_raw_hex']
  for sy in symbols.values():
   if sy['section']==section and sy['name']in required:
    value=whole['address']+sy['value'];assert sy['name']not in res or res[sy['name']]==value;res[sy['name']]=value
 assert set(res)==required and len(required)==13
 PE=load(R/'tools/analysis/pe.py','CRT_transition_pe');crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes());declarations=[];control=[]
 for i,row in enumerate(old):
  row=dict(row);pc=row['pc'];target=res[row['symbol']];width=len(bytes.fromhex(row['original_hex']));row['instrumented_hex']=(struct.pack('<I',target)if row['kind']=='registry-IAT'else b'\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\x90'*(width-5)).hex();row['compiled_target']=target
  if row['kind']=='registry-IAT':
   row['original_hex']=None;row['runtime_input_requirement']='Exactly owning named GetProcAddress export from current CRT constructor-input/named-API-bindings 7DWORD row, physical staged import and actual loaded owner/forwarder PE proof; not old capture literal.';sample={**row,'original_hex':struct.pack('<I',0x71000000+i*16).hex()}
  else:
   offset,_=crt.rva_range(pc-crt.image_base,width);assert crt.data[offset:offset+width].hex()==row['original_hex'];sample=dict(row)
  declarations.append(row);control.append(sample)
 body=pin(base/'reference.cpp').read_text();remove=body.index('if(mfc_phase){require(phase==15');restore=body.index('reinstall_registry_hooks();install_CRT_hooks();}',remove);after=body.index('copy_pages(r->memory_after)',remove);assert remove<after<restore
 # Constructor shim/code restoration precedes every phase AFTER code/IAT full-page snapshot.
 ctor_install=body.index('if(constructor_phase){const unsigned actual=dword(0x5bb4bc)');ctor_restore=body.index('"Restore exact original823 named target"',ctor_install);ctor_copy=body.index('copy_pages(r->memory_after)',ctor_restore);crt_after=body.index('"/CRT-after/"',ctor_copy);extra_after=body.index('"/extra-after/"',crt_after);assert ctor_install<ctor_restore<ctor_copy<crt_after<extra_after
 assert body.index('*reinterpret_cast<unsigned*>(0x5bb4bc)=ctor_MFC_target',ctor_restore)<ctor_copy and body.index('std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size)',ctor_restore)<ctor_copy
 fs=json.loads(pin(base/'fs-hook-bindings.json').read_bytes());assert len([r for r in fs if r['PC']>=0x78000000])==3;assert all(r['declared_observer']in res or '_'+r['declared_observer']in res for r in fs if r['PC']>=0x78000000)
 helper=pin(R/'tools/m4-141-consumer-review/mfc_transition141_v1.py');s=helper.read_text();deltas=json.loads(pin(out/'helper-deltas.json').read_bytes());assert len(deltas)==2
 for d in reversed(deltas):assert s.count(d['new'])==1;s=s.replace(d['new'],d['old'])
 assert s==pin(R/'tools/m4-startup138-original/mfc_transition_v1.py').read_text();T=load(helper,'current_CRT13_transition')
 def failure(name,fn):
  try:fn()
  except ValueError:checks.append(dict(passed=True,name=name));return
  raise AssertionError(name+' accepted')
 pages=sorted({r['pc']&~4095 for r in control})
 for page in pages:
  a=bytearray([0x5a]*4096);z=bytearray(a)
  for row in control:
   if row['pc']&~4095==page:
    n=row['pc']&4095;x=bytes.fromhex(row['original_hex']);y=bytes.fromhex(row['instrumented_hex']);a[n:n+len(x)]=x;z[n:n+len(y)]=y
  t=T.Transition(control);t.relation(bytes(z),bytes(a),page,15,0);t.relation(bytes(a),bytes(z),page,16,0);checks.append(dict(passed=True,name=hex(page)+' exact full-page remove/reinstall'))
  occupied={n for row in control if row['pc']&~4095==page for n in range(row['pc']&4095,(row['pc']&4095)+len(bytes.fromhex(row['original_hex'])))};offset=next(n for n in range(4096)if n not in occupied);wrong=bytearray(a);wrong[offset]^=1
  failure(hex(page)+' extra byte',lambda:T.Transition(control).relation(bytes(z),bytes(wrong),page,15,0));failure(hex(page)+' wrong prior mode',lambda:T.Transition(control).relation(bytes(a),bytes(a),page,15,0));failure(hex(page)+' unowned phase14',lambda:T.Transition(control).relation(bytes(z),bytes(a),page,14,0));failure(hex(page)+' incomplete page',lambda:T.Transition(control).relation(bytes(z)[:-1],bytes(a),page,15,0))
 failure('missing span',lambda:T.Transition(control[:-1]));failure('overlap span',lambda:T.Transition(control[:-1]+[control[0]]));checks.append(dict(passed=True,name='constructor9code+IAT restored before every actual endpoint; no generic constructor carry exception'))
 q=out/'patch-declarations.json';q.write_text(json.dumps(declarations,indent=2)+'\n');pin(q);pin(__file__)
 report=dict(passed=True,prepared_only=True,compiled_CRT_observer_spans=13,registry_IAT_spans=8,CRT_FS_spans=3,NULL_spans=2,remove_phase=15,reinstall_phase=16,complete4096_prior_mode_and_whole_output=True,controls=len(checks),checks=checks,constructor_temporary_code_and_IAT_restored_before_endpoint=True,constructor_endpoint_page_exemption=False,dynamic_named_target_gate_pending=True,current_full_original141_validator_pending=True,AFTER_seed=False,reader_opened=False,worker_launched=False,admitted=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),controls=len(checks))))
if __name__=='__main__':main()

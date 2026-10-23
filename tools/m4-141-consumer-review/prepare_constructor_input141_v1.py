"""Replace obsolete fixture address range with eight exact current linked shims."""
from pathlib import Path
import ast,copy,hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-original141/constructor-input141-preparation-r1';out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 proof=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/report.json','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c').read_bytes());assert proof['passed']
 for p,h in proof['files'].items():pin(p,h)
 links=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json').read_bytes());resolutions={}
 for row in links:
  for rel in row['relocations']:
   if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
    symbol,value=rel['symbol'],rel['actual_symbol_address'];assert symbol not in resolutions or resolutions[symbol]==value;resolutions[symbol]=value
 exact=tuple(resolutions['_registry_API_'+str(i)]for i in range(8));reference=next(row for row in links if row['symbol']=='reference_x86 whole source');assert len(set(exact))==8 and all(reference['address']<=v<reference['address']+reference['bytes']for v in exact)
 assert len(bytes.fromhex(reference['object_raw_hex']))==len(bytes.fromhex(reference['linked_hex']))==reference['bytes']
 parent=pin(R/'tools/m4-138-validation-review/constructor_input_capture_phase_v1.py');s=parent.read_text(encoding='utf-8');a='and 0x18000000<=shim<0x19000000';b='and shim==EXACT_SHIMS[i]';assert s.count(a)==1;s=s.replace(a,b)
 anchor='import struct\n';addition=anchor+'EXACT_SHIMS='+repr(exact)+'\n';assert s.count(anchor)==1;s=s.replace(anchor,addition);assert s.replace(addition,anchor).replace(b,a)==parent.read_text(encoding='utf-8');ast.parse(s)
 helper=R/'tools/m4-141-consumer-review/constructor_input141_v1.py';assert not helper.exists();helper.write_text(s,encoding='utf-8');pin(helper)
 old=pin(R/'tools/m4-141-consumer-review/validate_original141_v7.py');v=old.read_text(encoding='utf-8');deltas=[]
 for a,b in [("ROOT/'tools/m4-138-validation-review/constructor_input_capture_phase_v1.py'","ROOT/'tools/m4-141-consumer-review/constructor_input141_v1.py'"),("ROOT/'reports/m4-original141/root-strict-reader-admission-r1/report.json'","ROOT/'reports/m4-original141/root-strict-reader-admission-r2/report.json'")]:
  assert v.count(a)==1;v=v.replace(a,b);deltas.append(dict(old=a,new=b))
 inverse=v
 for d in reversed(deltas):assert inverse.count(d['new'])==1;inverse=inverse.replace(d['new'],d['old'])
 assert inverse==old.read_text(encoding='utf-8');ast.parse(v);validator=R/'tools/m4-141-consumer-review/validate_original141_v8.py';assert not validator.exists();validator.write_text(v,encoding='utf-8');pin(validator)
 # Evaluate the actual entire production binding predicate, not a copied predicate.
 tree=ast.parse(s);predicate=next(n.test for n in ast.walk(tree)if isinstance(n,ast.Assert)and 'EXACT_SHIMS' in ast.unparse(n.test));expr=compile(ast.Expression(predicate),str(helper),'eval');cells=(0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040);controls=[]
 def test(name,e,want):
  try:got=bool(eval(expr,e))
  except (KeyError,IndexError,TypeError):got=False
  assert got==want,name;controls.append(dict(name=name,passed=True,expected_accept=want))
 for i in range(8):
  env=dict(i=i,kind=i,cell=cells[i],raw=exact[i],shim=exact[i],shim_addresses=list(exact),EXACT_SHIMS=exact,CELLS=cells,target=0x77700000+i,declared=0x77700000,owner=0x77700000)
  test('current_exact_kind_'+str(i),env,True)
  for field in ('kind','cell','raw','shim','target','declared','owner'):
   e=copy.deepcopy(env);e[field]=0 if field in ('target','declared','owner')else e[field]+1;test('reject_'+field+'_'+str(i),e,False)
  e=copy.deepcopy(env);e['shim_addresses'][i]+=1;test('reject_passed_wrong_identity_'+str(i),e,False)
  e=copy.deepcopy(env);e['raw']=e['shim']=e['shim_addresses'][i]=0x18010000+i*16;test('reject_consistent_old_fixture_'+str(i),e,False)
 before=next(n.test for n in ast.walk(tree)if isinstance(n,ast.Assert)and 'before[2013454336]' in ast.unparse(n.test)) if False else None
 # Pin actual current success, both strict failures, immutable capture gate and old new-reader gate.
 for p,h in [('root-capture-execution-r2/report.json','2897d2f5e3a6607e1609ea15a661a0cc76bffd12e2c9017a5b2993c7bb590820'),('root-capture-admission-r2/report.json','2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697'),('root-capture-validation-r2/report.json','ee27047f17db5e6b6828660564ed61af918386088a2b1e1d91d6bc392a64af6c')]:pin(R/'reports/m4-original141'/p,h)
 prior=pin(R/'reports/m4-original141/root-strict-reader-admission-r1/report.json','dcc4268650b1298b0d96321199b8a85fef8417d63ace08b979ddf483147a57f0');admission=json.loads(prior.read_bytes())
 for p,h in admission['files'].items():pin(p,h)
 pin(R/'reports/m4-original141/root-capture-validation-r2/failure.txt');pin(__file__)
 artifact=out/'finite-deltas.json';artifact.write_text(json.dumps(dict(helper=[dict(old=anchor,new=addition),dict(old='and 0x18000000<=shim<0x19000000',new='and shim==EXACT_SHIMS[i]')],validator=deltas),indent=2)+'\n',encoding='utf-8');pin(artifact)
 p=out/'controls.json';p.write_text(json.dumps(controls,indent=2)+'\n',encoding='utf-8');pin(p)
 p=out/'current-reader-input-union.json';p.write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');pin(p)
 report=dict(passed=True,prepared_only=True,helper_two_delta_inverse=True,validator_two_binding_inverse=True,exact_current_shims=list(exact),whole_reference_ASM_span=dict(address=reference['address'],bytes=reference['bytes']),controls=len(controls),retained_all_typed_input_guards=True,new_reader_admission_path=str(R/'reports/m4-original141/root-strict-reader-admission-r2/report.json'),capture_preflight_path=str(R/'reports/m4-original141/root-capture-admission-r2/report.json'),capture_preflight_sha256='2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697',worker_relaunch_required=False,canonical_reader_opened=False,worker_launched=False,initializer_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(p),validator_sha256=sha(validator),helper_sha256=sha(helper),controls=len(controls),inputs=len(files))))
if __name__=='__main__':main()

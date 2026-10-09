"""Authenticate the independent bootstrap model against a saved current worker."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
import provider_bridge as P
import provider_capture as C
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(capture,digest,name):
 out=ROOT/'reports/m4-onexit-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};passed=False;counts={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);P.I.need(h is None or v==h,'Physical pinned independent dependency '+str(p));pins[str(p)]=v;return p
 try:
  capture=pin(capture,digest)
  G=load('bootstrap_validated_game',pin(ROOT/'tools/m4-onexit-source/game_model.py'))
  proof=json.loads(pin(ROOT/'reports/m4-onexit-source/original-game-source-r2/report.json','e3854a8ceaaab3461a27fc45bf8a426378241d298096ec9ec405d81f67d94a5c').read_bytes());P.I.need(proof['passed']and proof['files'][str(ROOT/'tools/m4-onexit-source/game_model.py')]==sha(ROOT/'tools/m4-onexit-source/game_model.py'),'Original-validated exact GameMachine')
  D=load('bootstrap_validated_capture',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));E=load('bootstrap_physical_export',pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'))
  a=D.DirectSet(capture,pin)
  try:
   stem='sequence-0/selected/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)
   static=out/'static';static.mkdir();material=P.material(static,pin);program,callbacks=G.source_program()
   m,responses=P.bootstrap(before,facts,heap,material,G.Machine,program,callbacks,oldpc,oldsp)
   actual=C.checkpoint(a,index,'registry-bootstrap-returned')
   P.I.need(bytes(m.state)==actual['state']and m.fx==actual['fx']and m.cpu==actual['cpu'],'All3504State/512FX/40CPU bootstrap returned fields from BEFORE only')
   for address,observed in actual['memory'].items():P.I.need(m.bytes(address,len(observed))==observed,'Entire independently predicted bootstrap owned/page bytes '+hex(address))
   for service,name_ in (('create','HeapCreate'),('query','GetVersionExA')):
    b=E.identity(a,stem+'heap-'+service+'-api-before',pin);z=E.identity(a,stem+'heap-'+service+'-api-after',pin);P.I.need(b==z,'Actual bootstrap API identity unchanged');rva,forward=E.export(Path(b[2]),name_);P.I.need(not forward and b[1]+rva==b[0],'Actual physical direct owning bootstrap export')
   for n in range(5):
    prefix=stem+'locale-api-'+str(n);b=E.identity(a,prefix+'-identity-before',pin);z=E.identity(a,prefix+'-identity-after',pin);raw=a.data(prefix+'-export-before.bin');P.I.need(b==z and raw==a.data(prefix+'-export-after.bin'),'Actual bootstrap allocator/static-CS identities unchanged');E.export_proof(raw,b,facts[n]['name'],pin)
   counts=dict(sequence=0,complete_State_bytes=3504,complete_FX_bytes=512,complete_CPU_bytes=40,entire_captured_pages=len(actual['memory']),typed_static_and_producer_APIs=responses.index,actual_bootstrap_API_identity_proofs=7,predicted_source_instructions=len(m.PCs),source_accesses=len(m.accesses),declared_minimal_TIB_maps=4)
   for module in list(sys.modules.values()):
    path=getattr(module,'__file__',None)
    if path:
     path=Path(path).resolve()
     if path.is_relative_to(ROOT/'tools')and path.is_file():pin(path)
   pin(__file__);passed=True
  finally:a.close()
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Current saved worker bootstrap only: authentic original BEFORE predicts genuine source heap-mode return, four real static-CS calls, sentinel stores and real128-byte producer allocation. The enclosing selected54 run is incomplete and contributes no initializer credit.',counts=counts,AFTER_machine_seed=False,API_fact_scope='Finite actual typed scalar/owned bytes; captured AFTER State/CPU/FX/pages/stack are comparison observations only',TIB_scope='Explicit minimal Runtime constructor input policy; not an observed original OS TEB',enclosing_selected54_acceptance=False,initializer_credit=False,files=pins)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])

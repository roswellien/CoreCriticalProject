"""Pure literal fps game/vsprintf adapter from genuine normal BEFORE exports."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-fps-original';T=Path(__file__).resolve().parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact pure source hunk '+a[:90]);return s.replace(a,b,1)
def main(name):
 out=B/name;need(not out.exists(),'Fresh fps pure source preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture archives');v=sha(p);need(h is None or h==v,'Physical identity '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 actual=read(B/'validation-r1/report.json','b43b40e24463f85fa3aff09d4fadc95d178761bdb658843f322fb1a1896ac8c6');need(actual['passed']and actual['all_reader_aliases_closed'],'Current genuine closed fps inputs')
 font=read(R/'reports/m4-font479590-original/source-r1/report.json','7a5b070228618400a1a4524b4df4214226f12c2570bcff9775fc6416265c4e9b');need(font['passed'],'Frozen literal font6 parent')
 worker=read(B/'preparation-r1/normal-contracts.json');c=copy.deepcopy(read(R/'reports/m4-font479590-original/source-preparation-r1/source-contracts.json'));known={r['pc']:r for r in c['instructions']};new=[]
 for row in worker['instructions']:
  if row['pc']not in known:new.append(row);known[row['pc']]=row
 need(len(new)==54 and sum(v['width']for v in new)==205,'Exact additive physical FPS game rows');c['instructions']+=new
 # The previously unadmitted shared CALL5A2F86 now has a literal same-instance
 # FPS vptr provenance; no old null-format root reaches that CALL.
 binding=next(v for v in c['source_indirect_contracts']if v['CALL_pc']==0x5a2f86);binding.update(worker['fps']['new_virtual']);binding.update(slot_offset=0x20,object_role='Current FPS instance5FC378 from literal base vptr store5A0114; observed root BEFORE and whole source object endpoints remain independent inputs/joins')
 registration=next(v for v in worker['roots']if v['root']==0x40f000);c['selected_roots'].append(dict(entry=0x40f000,slot=0x5e0050,object=0x5fc378,registration=dict(callback=registration['callback'],push_PC=registration['push_PC'],CALL_pc=registration['CALL_pc'],return_PC=registration['return_PC']),measured=False))
 A=load(R/'tools/m4-service-initializers/recover.py','fps_physical_vsprintf');D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','fps_descriptor_parser');crt=A.Module(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',A.IDENTITIES['local/mw3-staged/Shared_DLLs/MSVCRT.DLL']))
 lookup=pin(R/'reports/m4-service-initializers/static-r1/MSVCRT.DLL.linear-lookup.txt')
 for line in lookup.read_text().splitlines():
  m=A.ROW.match(line)
  if m:
   pc=int(m[1],16);b=bytes.fromhex(m[2]);asm=re.sub(r'\s+',' ',m[3].strip());op,_,args=asm.partition(' ');crt.rows[pc]=dict(pc=pc,size=len(b),bytes=b.hex(),mnemonic=op,operands=args)
 graph=A.walk(crt,0x780230dd);need(graph['local_decode_closed'],'Whole actual vsprintf physical graph')
 provider=[]
 for row in graph['instructions']:
  pc=row['pc'];b=bytes.fromhex(row['bytes']);off,_=crt.image.rva_range(pc-crt.base,len(b));need(crt.image.data[off:off+len(b)]==b,'Physical whole vsprintf source row')
  provider.append(D.instruction_contract(dict(pc=pc,width=len(b),bytes_hex=b.hex(),mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0])))
 c['instructions']+=provider;c.update(schema='mw34-fps-literal-source-v1',source_prefix_only=True,source_registration_provider_executed=False,real_fps_formatter40F000_admitted=True,vsprintf_domain='Actual finite narrow literal fps only; every reached provider PC must be present and derived from untouched source memory',source_after_seed=False)
 out.mkdir(parents=True);cp=out/'source-contracts.json';cp.write_text(json.dumps(c,indent=2)+'\n');pin(cp);gp=out/'vsprintf-physical-graph.json';gp.write_text(json.dumps(graph,indent=2)+'\n');pin(gp)
 parent=pin(R/'reports/m4-font479590-original/source-preparation-r1/game_model.py');model=parent.read_text();model=one(model,"def contracts():return frozen('reports/m4-font479590-original/source-preparation-r1/source-contracts.json','97792d1f89cf5b66debbcf456bc5d4467cf0e685829de449ef421d18e37b0d2d')","def contracts():return frozen('"+cp.relative_to(R).as_posix()+"','"+sha(cp)+"')")
 model=one(model,"  if pc==0x5a2f40:I.need(self.bytes(self.reg('esp')+8,4)==bytes(4),'Current literal null format argument')","  if pc==0x5a2f40:\n   format_=int.from_bytes(self.bytes(self.reg('esp')+8,4),'little')\n   if self.widget_root==0x40f000:I.need(format_==0x5e1590 and self.bytes(format_,4)==b'fps\\0','Genuine finite physical nonnull fps source argument')\n   else:I.need(format_==0,'Current other-widget literal null format argument')")
 model=one(model,'  imports={0x5a013c:',"  if original_pc==0x5a2f68:\n   I.need(self.widget_root==0x40f000 and size==4 and address==0x5bb53c,'Exact current FPS owning import')\n   response=self.widget_imports.get((original_pc,address));I.need(response and value==response['raw_value']and response['target']==0x780230dd,'Own raw FPS observer IAT and named staged vsprintf target')\n   self.widget_import_reads.append(dict(root=self.widget_root,PC=original_pc,slot=address,raw_value=value,target=response['target'],source_access_index=len(self.accesses)-1));return response['target']\n  imports={0x5a013c:")
 mp=out/'game_model.py';mp.write_text(model);pin(mp)
 comp=pin(R/'tools/m4-font479590-original/compare_source.py','abe34826fa320264f5c6646628a17db6370a409d3005a5b20931ebb1024d5dbf').read_text()
 comp=comp.replace("reports/m4-font479590-original","reports/m4-fps-original").replace('3b5e6b93cd4f6600c765666d9489bf28e821aa5269ec7c522e849a75a0e972a9','b43b40e24463f85fa3aff09d4fadc95d178761bdb658843f322fb1a1896ac8c6')
 comp=one(comp,'results=[];API_inputs=[];memory_joins=[]','results=[];API_inputs=[];memory_joins=[];FPS_joins=[]')
 comp=one(comp,"        boundaries=read(validation_path.parent/'actual-GDI-boundaries.json'","        FPS=read(validation_path.parent/'actual-FPS-boundaries.json',validation['files'][str((validation_path.parent/'actual-FPS-boundaries.json').resolve())]);fps_identity=u(capture('fps/identity.bin'),0,4)\n        boundaries=read(validation_path.parent/'actual-GDI-boundaries.json'")
 comp=one(comp,'            boundary_index=[0];fs_index=[0];','            fpsfacts=[v for v in FPS if v[\'phase\']==phase];fps_index=[0];imports[(0x5a2f68,0x5bb53c)]=dict(raw_value=u(memory[0x5bb000],0x53c)[0],target=fps_identity[1])\n            boundary_index=[0];fs_index=[0];')
 inc=pin(T/'fps_source_join.inc');comp=one(comp,'            def fs(model,event,data):',inc.read_text()+'            def fs(model,event,data):')
 comp=one(comp,'                    pc=self.cursor\n','                    pc=self.cursor\n                    if fps_index[0]<len(fpsfacts)and pc==fpsfacts[fps_index[0]][\'CPU\'][9]:fps_boundary(self,fpsfacts[fps_index[0]]);fps_index[0]+=1\n')
 comp=one(comp,"boundary_index[0]==len(facts)and fs_index[0]==len(fsfacts)","boundary_index[0]==len(facts)and fs_index[0]==len(fsfacts)and fps_index[0]==len(fpsfacts)")
 comp=one(comp,'source_callback_execution=False,unused_observed_API_stack_bytes=dead_stack','source_callback_execution=False,FPS_joins=fpsfacts,provider_dispatches=machine.output_dispatches,unused_observed_API_stack_bytes=dead_stack')
 comp=one(comp,"counts['literal_widget_registration_prefixes']==6", "counts['literal_widget_registration_prefixes']==7 and counts['literal_FPS_CPU_FX_ENV_frame_joins']==2 and counts['literal_FPS_provider_instructions']>0")
 comp=one(comp,"(('source-derivations.json',results)","(('literal-FPS-joins.json',FPS_joins),('source-derivations.json',results)")
 comp=one(comp,"pin(R/'tools/m4-fps-original/prepare_source.py');","pin(R/'tools/m4-fps-original/prepare_source.py');pin(R/'tools/m4-fps-original/fps_source_join.inc');pin(R/'tools/m4-font479590-original/compare_source.py');")
 comp=comp.replace('Literal carried five-widget plus479590 normal registration prefixes','Literal carried seven-root widget/font/fps registration prefixes including complete finite vsprintf source')
 qp=T/'compare_source.py';need(not qp.exists(),'Fresh pure FPS comparer');qp.write_text(comp);pin(qp);pin(__file__)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Pure literal original FPS game/vsprintf source preparation; actual comparison pending',counts=dict(roots=7,new_game_rows=len(new),new_game_bytes=205,vsprintf_rows=len(provider),vsprintf_bytes=sum(v['width']for v in provider)),genuine_validation_sha256=sha(B/'validation-r1/report.json'),contracts_sha256=sha(cp),model_sha256=sha(mp),comparer_sha256=sha(qp),source_after_seed=False,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),provider_rows=len(provider))))
if __name__=='__main__':main(sys.argv[1])

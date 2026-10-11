"""Strict isolated native tree comparison from bootstrap BEFORE, never root AFTER."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-lockit-source'));sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_bridge as B
import bridge_v2 as B2
import capture as C
PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000)
def need(x,s):
 if not x:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();d=hashlib.sha256(p.read_bytes()).hexdigest();need(h is None or d==h,'Exact physical source '+str(p));PINS[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def equal(a,b,s):need(a==b,s+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:8]))
def projection(n,state):
 fx,env=n.proj(state);return fx[:6]+bytes(18)+fx[24:],env
def main(name):
 out=ROOT/'reports/m4-tree-source'/name;need(not out.exists(),'Fresh isolated source gate');out.mkdir(parents=True);passed=False;reader=None;counts=collections.Counter();results=[]
 try:
  receipt=read(ROOT/'reports/m4-tree-review/fixture-execution-r3/report.json','14c2c858fb1fd024c35bb4e50419d1b0935a7d3e11820b9817f738fe6884bf3d');need(receipt['passed'],'Both actual native fixture levels succeeded');build=read(receipt['build_path'],receipt['build_sha256']);prep=read(receipt['native_preparation'],receipt['native_preparation_sha256'])
  G=load('isolated_tree_model',ROOT/'tools/m4-tree-source/game_model_v4.py');R=load('isolated_tree_responses',ROOT/'tools/m4-tree-source/responses125.py');R.EXPECTED_LOCKIT_CALLS=26
  class Responses(R.ActualResponses):
   def __call__(self,m,target):
    mfc=any(f[0]in(0x5abd26,0x5f401ea0)for f in m.call_stack);count=len(self.allocations);super().__call__(m,target)
    if len(self.allocations)>count and mfc:self.allocations[-1]['kind']=4
  R.ActualResponses=Responses;B.R=R
  D=load('isolated_tree_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('isolated_tree_numeric_projection',ROOT/'tools/m4-joint-startup27-review/observe.py');n,_,_,_=J.models();n.PAGES=list(PAGES)
  PE=load('isolated_tree_PE',ROOT/'tools/analysis/pe.py');game=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());cpraw=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes();cp=PE.PEImage(cpraw)
  rw=pin(prep['loaded_input_page'],prep['loaded_input_page_sha256']).read_bytes();iat=pin(prep['loaded_IAT_page'],prep['loaded_IAT_page_sha256']).read_bytes()
  def initial(page):
   if page==0x78145000:return rw
   if page==0x78146000:return iat
   if page==0x780c1000:return cpraw[0x1000:0x2000]
   if page==0x78115000:return cpraw[0x54c00:0x55c00]
   if page==0x5f498000:return pin(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-raw-page.bin','751e6229f4c61085d8e23814a5079e40fa99d411bd0f50ceb010f56d753b2d67').read_bytes()
   need(page!=0x20001000,'Bootstrap supplies genuine whole stack BEFORE');pe=cp if page==0x7810a000 else mfc if page==0x5f4cc000 else game;b=bytearray(4096)
   for sec in pe.sections:
    lo=max(page,pe.image_base+sec['virtual_address']);hi=min(page+4096,pe.image_base+sec['virtual_address']+sec['raw_size'])
    if hi>lo:offset=sec['raw_offset']+lo-pe.image_base-sec['virtual_address'];b[lo-page:hi-page]=pe.data[offset:offset+hi-lo]
   return bytes(b)
  static=out/'static';static.mkdir();material=B.material(static,pin);program,callbacks=G.source_program()
  for level in('O0','O2'):
   reader=D.DirectSet(receipt['workers'][level]['transport'],pin);stem='actual-cleaned/';index=C.checkpoints(reader,stem);before,facts,heap,pc,sp=C.bootstrap_inputs(reader,stem,index)
   before['memory']=dict(before['memory'])
   for page in PAGES:
    if page not in before['memory']:before['memory'][page]=initial(page)
    if page in(0x7810a000,0x78145000,0x78146000):equal(before['memory'][page],initial(page),'Entire original loaded provider input')
   seen=[]
   class Observed(G.Machine):
    def snapshot(self,name):
     if name=='registry-producer-before':need(self.cursor==0x5ac3ec and self.word(2472)==0x5ac3e2,'Literal producer stop projection');self.word(2472,self.cursor)
     super().snapshot(name)
     if name in index:
      actual=C.checkpoint(reader,index,name);equal(bytes(self.state),actual['state'],'Entire source-derived checkpoint State '+name);equal(B.cpu(self.state),actual['cpu'],'Entire source checkpoint CPU '+name);equal(self.fx,actual['fx'],'Entire source checkpoint FX '+name)
      for page,raw in actual['memory'].items():equal(self.bytes(page,len(raw)),raw,'Whole source checkpoint page '+name+' '+hex(page))
      seen.append(name);counts['whole_provider_checkpoints']+=1
   resource=reader.words(stem+'lockit-resource.bin',8,'Q');raw=reader.data(stem+'lockit-native-images.bin');need(len(raw)==26*40,'Exact13 source pairs in isolated tree');images=[raw[i:i+40]for i in range(0,len(raw),40)]
   def associate(machine,responses):
    machine.snapshot('lockit-resource-association-before');responses.associate_lockit(machine,resource,images,rw[0x640:0x658]);machine.snapshot('lockit-resource-association-after')
   machine,responses=B2.bootstrap(before,facts,heap,material,Observed,program,callbacks,pc,sp,resource_association=associate)
   cpu=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001804,0x92837465,0x56473829,0xaabbccdd,0x202,0x410a80);n.statecpu(machine.state,cpu);machine.cursor=0x410a80;machine.cpu=struct.pack('<10I',*cpu);machine.fx=projection(n,machine.state)[0]
   G.begin_root(machine,0x4b7f70);machine.cpu=B.cpu(machine.state);record=reader.data('actual-root-records.bin');need(len(record)==159716,'Exact native root Record geometry');equal(bytes(machine.state),record[141540:145044],'Full3504B literal BEFORE state');equal(machine.cpu,record[36:76],'Full40B source CPU BEFORE');fx,env=projection(n,machine.state);equal(fx,record[116:628],'FullFX source BEFORE');equal(env,record[2164:2192],'WholeENV source BEFORE')
   for page in PAGES:equal(machine.bytes(page,4096),reader.data('actual-before-root/current-page-'+str(page)+'.bin')if page!=0x20001000 else record[2276+PAGES.index(page)*4096:2276+(PAGES.index(page)+1)*4096],'Whole persistent source BEFORE page '+hex(page));counts['whole_BEFORE_pages']+=1
   G.complete_root(machine,api=responses);machine.cpu=B.cpu(machine.state);machine.fx=projection(n,machine.state)[0];result=machine.tree_result()
   equal(bytes(machine.state),record[145044:148548],'Full3504B literal AFTER State');equal(machine.cpu,record[76:116],'Whole40B literal AFTER CPU');fx,env=projection(n,machine.state);equal(fx,record[628:1140],'WholeFX literal AFTER');equal(env,record[2192:2220],'WholeENV literal AFTER')
   for page in PAGES:equal(machine.bytes(page,4096),reader.data('actual-after-root/current-page-'+str(page)+'.bin'),'Entire4096B AFTER page including whole native stack '+hex(page));counts['whole_AFTER_pages']+=1
   actual_accesses=list(struct.iter_unpack('<IIQII',reader.data('actual-after-root/locale-source-accesses.bin')));equal([tuple(r)for r in machine.accesses],actual_accesses,'Entire bootstrap and tree source access ledger');counts['whole_source_access_records']+=len(actual_accesses)
   responses.lockit_complete();relations=load('isolated_tree_native_relations',ROOT/'tools/m4-tree-source/native_tree_relations.py');counts.update(relations.verify(reader,'actual-after-root/',result,responses.lockit_relations,C,index));need(len(result['owned_accesses'])==172 and len(result['owners'])==len(result['publications'])==7 and len(result['Lockit_calls'])==26 and len(result['FS_frames'])==7,'Exact repeated dynamic source extent')
   for owner in result['owners']:
    generation=owner['generation'];equal(bytes.fromhex(owner['source_final_hex']),reader.data('actual-after-root/native-full-'+str(generation)+'.bin'),'Entire actual native acquired owner capacity including untouched tail');counts['whole_native_owner_backings']+=1
   result['level']=level;result['compared_checkpoints']=seen;result['actual_native_API_relations']=responses.lockit_relations;results.append(result);counts['strict_native_levels']+=1
   reader.close();reader.entries.clear();reader.bundles.clear();reader=None
  for module in(n,J):
   for p,h in getattr(module,'PINS',{}).items():pin(p,h if isinstance(h,str)else h['sha256'])
  for p in(ROOT/'tools/m4-lockit-source/capture.py',ROOT/'tools/m4-lockit-source/bridge_v2.py',ROOT/'tools/m4-onexit-review/provider_bridge.py',ROOT/'tools/m4-onexit-review/provider_capture.py',ROOT/'tools/m4-onexit-review/provider_responses_v2.py',ROOT/'tools/m4-onexit-review/provider_responses.py',Path(__file__)):pin(p)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()
  (out/'source-derivations.json').write_text(json.dumps(results,indent=2)+'\n');pin(out/'source-derivations.json');report=dict(passed=passed,scope='Isolated actual native O0/O2 compared with persistent literal bootstrap/tree from bootstrap BEFORE and bounded API responses; whole stack/State/CPU/FX/ENV and full actual native owner capacity',counts=dict(counts),candidate_AFTER_machine_seed=False,root_BEFORE_machine_seed=False,native_whole_stack_compared=True,reader_closed=True,initializer_credit=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])

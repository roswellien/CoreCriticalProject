"""Supplemented actual original18 own literal source and complete endpoint gate."""
from pathlib import Path
import json,hashlib,importlib.util,struct,traceback,sys
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};a=None;passed=False;cases=[];stage={}
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def write(p,v):p.write_text(json.dumps(v,indent=2,default=lambda v:v.hex()));pin(p)
 try:
  V=json.loads(pin(R/'reports/m4-138-validation-review/constructor-input-capture-validation-r2/report.json','aec13bc32dc8a0a02b5d9fd63d999e52c82bef8e9d63dbee8f74b330a786469f').read_bytes());assert V['passed']and V['reader_closed'];E=load('tools/m4-joint-startup131/paired_exports.py','ex');A=load('tools/m4-138-validation-review/constructor_original_input_v5.py','adapter');D=load('tools/m4-constructor-native/derive_source_v9.py','derive');preparation=pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json','26b896f0523439030cbdd6cf4bd98cfadfbb9b15451bf80950600c37db892e6e');program,_=D.M.source_program(preparation);provider_proof=json.loads(pin(R/'reports/m4-138-validation-review/constructor-provider-named-proof-r1/report.json','0bfde9d0b381efd15ed762cb8ecb81a79a61a26f7a9439f3c3897f6a21aef6ec').read_bytes());a=E.Facade(V['paired_exports'][0],pin)
  for seq in range(6):
   for root in(0x4103f0,0x410440,0x459b40):
    phase={0x4103f0:13,0x410440:14,0x459b40:36}[root];stem=f'phase/{seq}/{phase}';case=out/f'original-{seq}-{root}';case.mkdir();stage=dict(sequence=seq,root=root,operation='own input');inp=A.build(a,seq,root,program,provider_proof);write(case/'input.json',inp);stage['operation']='literal source';result=D.derive(inp,preparation);write(case/'source-derivation.json',result)
    # All root endpoint comparisons start only after literal computation terminates.
    stage['operation']='exact ordered source observer PUSHFD boundary joins';normal=a.data('constructor-prerequisites/'+stem+'/normal/normal-records.bin');assert len(normal)%189108==0;observed=[]
    for i in range(len(normal)//189108):
     n=normal[i*189108:(i+1)*189108];meta=struct.unpack_from('<12I',n);cpu=struct.unpack_from('<10I',n,48);observed.append((meta,cpu,n[88:600]))
    events=result['original_observer_stores'];assert len(events)==len(observed)
    for e,(meta,cpu,fx)in zip(events,observed):
     assert (meta[0],meta[2],meta[3],meta[4],meta[5])==(1,root,e['kind'],e['source_PC'],e['CPU'][4]);assert tuple(e['CPU'])==cpu and bytes.fromhex(e['FX512_hex'])==fx;assert e['address']==cpu[4]-4 and e['source_EFLAGS']==cpu[8]and e['write_hex']==struct.pack('<I',cpu[8]).hex()
    stage['operation']='CPU endpoint';raw=a.data(stem+'.bin');actual=struct.unpack_from('<10I',raw,76);expected=result['source_computed_CPU'];assert tuple(expected[:8])==actual[:8]and expected[9]==actual[9];undefined=result['source_remaining_undefined_flags'];mask=sum(1<<D.M.BITS[k]for k in undefined);assert (expected[8]^actual[8])&~mask==0
    stage['operation']='whole FX/ENV endpoint';assert bytes.fromhex(result['source_computed_FX_hex'])==raw[628:1140];assert raw[2164:2192]==raw[2192:2220]
    memory={int(k):bytes.fromhex(v)for k,v in result['source_computed_memory'].items()};pages={page:raw[178404+i*4096:178404+(i+1)*4096]for i,page in enumerate(A.PAGES)}
    for key in a.entries:
     if key.startswith(stem+'/extra-after/'):pages[int(key.rsplit('/',1)[1][:-4])]=a.data(key)
    pages[0x5f2000]=a.data('constructor-prerequisites/'+stem+'/AFTER-constructor/5F2000.bin')
    for page,flags,typ in A.rows(a.data(stem+'/CRT-image/metadata.bin'),3):pages[page]=a.data(stem+'/CRT-image/after/'+str(page)+'.bin')
    assert result['observer_source_memory_changed']is False;memory[0x20001000]=bytes.fromhex(result['source_instrumented_upper_stack_hex'])
    stage['operation']='whole page endpoints';diffs=[]
    for page,b in sorted(pages.items()):
     assert page in memory and len(memory[page])==len(b)==4096
     if memory[page]!=b:diffs.append(dict(page=page,count=sum(x!=y for x,y in zip(memory[page],b)),first=[dict(offset=i,source=x,actual=y)for i,(x,y)in enumerate(zip(memory[page],b))if x!=y][:16]))
    if diffs:write(case/'page-diffs.json',diffs);raise ValueError('Whole original page endpoint mismatch')
    stage['operation']='whole owned endpoints';prefix='constructor-prerequisites/'+stem+'/AFTER-owners/';live={};
    for key in a.entries:
     if key.startswith(prefix)and key.endswith('/meta.bin'):
      w=a.words(key,12);b=a.data(key[:-8]+'bytes.bin');assert w[9]==1 and len(b)==w[8];live[w[7]]=b
    source={v['guest']:v for v in result['source_complete_owners']if v.get('live',True)};assert set(source)==set(live)
    for guest,b in live.items():assert bytes.fromhex(source[guest]['source_final_hex'])==b
    cases.append(dict(sequence=seq,root=root,source_complete=True,whole_GPR_EIP=True,defined_EFLAGS=True,undefined_flags=undefined,whole_FX512=True,whole_ENV28=True,whole_page_regions=len(pages),exact_source_observer_PUSHFD_joins=len(events),observer_live_read_transparency=result['original_observer_live_stack_read_checks'],observer_undefined_flag_domains=[e['source_undefined_flags']for e in events],whole_owned_backings=len(live),source_APIs=result['source_API_inputs'],source_AFTER_seed=False,original_State_equality_claim=False))
  assert len(cases)==18
  seen=set()
  def modules(m):
   if id(m)in seen:return
   seen.add(id(m));file=getattr(m,'__file__',None)
   if file and Path(file).resolve().is_relative_to(R):pin(file)
   import types
   for value in vars(m).values():
    if isinstance(value,types.ModuleType)and getattr(value,'__file__',None)and Path(value.__file__).resolve().is_relative_to(R):modules(value)
  for module in(D,D.M,A,A.P):modules(module)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc())
 finally:
  if a:a.close()
  pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Current supplemented original18 literal constructors/MFC/CRT/providers from own complete BEFORE pages+descriptors and finite typed API observations; root targets opened after source terminates.',cases=cases,frontier=stage,canonical_reader_opened=False,ordinary_reader_closed=True,whole_original_State_claim=False,whole_TIB_claim=False,unexplained_stack_difference_allowed=False,source_AFTER_seed=False,initializer_credit=0,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])

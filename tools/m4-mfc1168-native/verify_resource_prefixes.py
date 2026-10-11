"""Causal source-prefix supplement using own positive BEFORE, never AFTER seeds.

Modes1/2 reject source-authored local read address/width mutations before the
accepted ledger. Their rejected payload is deliberately not claimed observed.
Mode10 retains its actual attempted write as one final explicit deviation.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:700])
def pin(p,h=None):
 p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable file');PINS[str(p)]=a;return p
def raw(p):return pin(p).read_bytes()
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Stop(Exception):pass
def main(execution,digest,source_path,source_sha,resource_path,resource_sha,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh causal source proof');out.mkdir();passed=False;counts=collections.Counter();rows=[]
 try:
  e=read(execution,digest);source=read(source_path,source_sha);resources=read(resource_path,resource_sha);need(e['passed']and source['passed']and resources['passed'],'Fresh positive complete source and all raw resource/refusal prerequisites');eq(source['execution_sha256'],digest,'Current source execution');eq(resources['execution_sha256'],digest,'Current resource execution');b=read(e['build'],e['build_sha256']);prep=read(b['preparation'],b['preparation_sha256']);c=read(prep['relocated_contracts']);layout=read(Path(b['preparation']).parent/'before-layout.json');policy=read(prep['relocation_proof']);positive=read(Path(source_path).parent/'source-derivations.json');program={r['pc']:r for r in c['instructions']};thread=next(o['new']for o in policy['owners']if o['role']=='thread');globalptr=next(o['new']for o in policy['owners']if o['role']=='global-object');guestCS=next(o['address']for o in layout if o['role']=='Borrowed initialized opaque guest CS24');guestThread=c['thread_contract']['current_process_thread']
  I=load(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','mfc_causal_integer');F=load(R/'tools/m4-formatting-source/flag_domain.py','mfc_causal_flags')
  class Literal(I.Machine):
   def cpu_now(self):
    flags=self.initial_flags
    for flag,bit in F.BITS.items():flags=(flags&~(1<<bit))|(int(bool(self.flag(flag)))<<bit)
    return tuple(self.reg(k)for k in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
   def step(self):
    if self.cursor==0x780014b4:
     need(self.call_stack[-1][0]==0x5f40107d and self.call_stack[-1][2]==0x5f4010b5,'Narrow literal imported EH return');self.call_stack.pop();outer=self.call_stack;self.call_stack=[]
     try:return super().step()
     finally:self.call_stack=outer
    return super().step()
  for item in e['controls']:
   mode,level=item['mode'],item['level'];p=Path(item['output']);base=Path(execution).parent/level;expected_source=next(r for r in positive if r['level']==level);initial=raw(base/'before/State.bin');cpu=raw(base/'before/CPU.bin');fx=raw(base/'before/FX.bin');memory={r['address']:raw(base/f'before/blocks/{r["address"]}.bin')for r in layout};expected_n={1:18,2:18,3:18,4:17,5:17,6:76,7:76,8:76,9:76,10:58,11:4,12:0}[mode];expected_apis={1:1,2:1,3:1,4:0,5:0,6:1,7:1,8:1,9:1,10:1,11:0,12:0}[mode]
   actual=list(struct.iter_unpack('<IIQII',raw(p/'accesses.bin')));eq(len(actual),expected_n,'Exact refused committed operand count');eq(len(raw(p/'APIs.bin')),expected_apis*352,'Exact refused completed source APIs')
   prefix=[tuple(x)for x in expected_source['source_accesses'][:expected_n]]
   if mode==10:prefix[-1]=(0x5ae3b7,globalptr+0x14,1,1,1)
   eq(actual,prefix,'Entire accepted literal source prefix and mode10 final attempted deviation');counts['whole_accepted_or_attempted_operand_rows']+=len(actual)
   context=struct.unpack('<12Q',raw(p/'retry/before/resource-context.bin'));eq(context[7:9],(expected_n,expected_apis),'Actual private cursors join measured prefix');eq(context[9:11],(1,0),'Actual entered incomplete source root');eq(context[2:4],(1,1),'Own live resources before cleanup')
   expected=(1,0,0)if mode==8 else(1,1,context[0])if mode==9 else(0,0,0);eq(context[4:7],expected,'Exact private depth versus actual native CS40 ownership at refusal')
   if mode!=12:
    def hook(m,event,data):
     if data.get('domain')=='source'and ((mode in(1,2,3)and event=='read-before'and len(m.accesses)==18)or(mode==10 and event=='write-before'and len(m.accesses)==57)):
      raise Stop()
    m=Literal(initial,fx,cpu,memory,program=program,callbacks={},hook=hook);m.initial_flags=struct.unpack_from('<I',cpu,32)[0];m.call_stack.append((0x5ae3e4,m.reg('esp'),0xfffffff0,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));api_index=0;domain={};stop=False
    try:
     while not stop:
      need(m.cursor in program,'Only normal literal source reaches refusal');domain=F.advance(m,program[m.cursor],domain);m.step()
      if mode==11 and m.PCs[-1]==0x5ae3db:stop=True;continue
      if m.cursor not in program:
       if (mode in(4,5)and api_index==0)or(mode in(6,7,8,9)and api_index==1):stop=True;continue
       need(api_index==0,'Only preceding actual typed TlsGetValue seam allowed');spec=c['normal_APIs'][0];eq(m.cursor,spec['source_target'],'Literal pre-refusal typed TLS source target');m.api_return(spec['source_PC'],spec['argc'],thread,[]);api_index+=1;domain={}
    except Stop:stop=True
    need(stop,'Exact source causal frontier reached');eq(len(m.accesses),57 if mode==10 else expected_n,'Exact modeled committed pre-refusal operand extent')
    if mode==3:m.word(2472,m.cursor+1);m.cursor+=1
    if mode==4:m.store_bytes(m.reg('esp')+4,struct.pack('<I',4))
    if mode==7:m.store_bytes(m.reg('esp')+4,struct.pack('<I',guestCS+4))
    eq(bytes(m.state),raw(p/'retry/before/State.bin'),'Complete source-derived causal refusal State3504');eq(struct.pack('<10I',*m.cpu_now()),raw(p/'retry/before/CPU.bin'),'Complete source-derived causal refusal guestCPU40');eq(m.fx,raw(p/'retry/before/FX.bin'),'Complete source-derived causal refusal guestFX512');counts['whole_source_refusal_State_CPU_FX_joins']+=1
    for row in layout:eq(m.bytes(row['address'],row['size']),raw(p/f'retry/before/blocks/{row["address"]}.bin'),'Whole source-derived causal refusal memory endpoint');counts['whole_source_refusal_memory_endpoints']+=1
   else:
    eq(raw(p/'retry/before/blocks/1598033920.bin')[0x83],0xcc,'Actual current physical source entry mutation retained');eq(actual,[],'Whole span rejection before any literal operand');counts['actual_code_span_refusals']+=1
   recorded_mutation={'mode':mode,'scope':'source-authored local mutation; rejected operand payload not captured'if mode in(1,2)else'current State/backing or attempted write observed', 'source_authored_mutation':dict(address=globalptr+4,width=4)if mode==1 else dict(address=thread+12,width=1)if mode==2 else None,'attempted_write':actual[-1]if mode==10 else None}
   rows.append(dict(level=level,mode=mode,accepted_source_operands=actual,expected_complete_APIs=expected_apis,resource_context=context,mutation=recorded_mutation,all_observed_retry_bytes_unchanged_prerequisite=resource_sha,no_AFTER_seed=True))
  (out/'causal-prefix-relations.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'causal-prefix-relations.json');pin(__file__);pin(sys.executable)
  for q,h in PINS.items():eq(sha(q),h,'Stable successful source/observation reads')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual twelve-refusal causal-prefix extension: own BEFORE literal model/complete StateCPUFX and284byteflow endpoints for eleven source-entered faults; exact source-span rejection separately; local rejected modes1/2 payload explicitly unobserved',execution=str(execution),execution_sha256=digest,source_receipt=str(source_path),source_receipt_sha256=source_sha,resource_receipt=str(resource_path),resource_receipt_sha256=resource_sha,counts=dict(counts),files=PINS,initializer_credit=0,capture_archive_reader_opened=False,all_bounded_readers_closed=True,source_AFTER_seed=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],Path(sys.argv[5]).resolve(),sys.argv[6],sys.argv[7])

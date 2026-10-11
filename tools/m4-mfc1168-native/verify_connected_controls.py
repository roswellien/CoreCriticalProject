"""Current connected public refusals, causal prefixes, full retry and lifetimes."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'));sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:350])
def main(execution,digest,name):
 out=ROOT/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh controls semantic gate');out.mkdir();pins={};passed=False;closed=True;counts=collections.Counter();cases=[];proofs={};identities=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 reasons={1:'Flat32',2:'literal physical source span',3:'physical raw import preimage',4:'TIB TLS mirror',5:'borrowed BEFORE',6:'borrowed BEFORE',7:'Guest access permission denied',8:'Guest access permission denied',9:'physical raw import preimage',10:'cached CRT additions',11:'causal connected source',12:'Flat32'}
 try:
  e=json.loads(pin(execution,digest).read_bytes());need(e['passed']and e['all_workers_terminal']and e['all_bounded_readers_closed'],'Actual current24 denials structural gate');b=json.loads(pin(e['build'],e['build_sha256']).read_bytes());p=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());need(p['control_cases']==12,'Exact current12 control input contract')
  for q,h in b['files'].items():pin(q,h)
  DS=load(ROOT/'tools/m4-crt-allocation-root/run_v2.py','mfc_causal_control_direct');V=load(ROOT/'tools/m4-mfc1168-native/verify_resource_fixture.py','mfc_causal_control_physical');V.PINS=pins
  MF=load(ROOT/'tools/m4-joint-startup131/mfc_source.py','mfc_causal_control_literal_adapter');extension=MF.Extension(p,pin);contracts=extension.contracts;literal=extension.literal
  for level in('O0','O2'):
   row=next(r for r in e['levels']if r['level']==level);a=DS.DirectSet(row['capture'],pin);closed=False
   try:
    for mode in range(1,13):
     stem=f'control-{mode}/';terminal=a.words(stem+'terminal-facts.bin',13);eq(terminal[:7],(1,mode,0,1,1,13,13),'Actual connected failure/poison/prior13 snapshot');has=bool(terminal[7]);reason=a.data(stem+'refusal.txt').decode();need(reasons[mode].lower()in reason.lower(),'Exact current reason at mode'+str(mode)+' '+reason)
     eq(a.words(stem+'facts.bin',8),(1,mode,13,1,1,1,1,int(has)),'Actual current refusal retry cleanup extent');counts['actual_precise_denials']+=1
     # Every raw private/context/route/page vector retained by the worker is
     # compared, not merely the four historical counters.
     for prefix in(stem+'retry-before/',stem+'MFC/retry-before/'):
      keys=[k for k in a.entries if k.startswith(prefix)];need(keys,'Complete captured retry scope')if prefix.endswith('retry-before/')and'/MFC/'not in prefix else None
      for key in keys:eq(a.data(key),a.data(key.replace('/retry-before/','/retry-after/')),'Entire unchanged poisoned retry '+key);counts['whole_retry_vectors']+=1
     for suffix in('caller-hardware.bin','retry-hardware.bin'):
      hw=a.data(stem+suffix);eq(len(hw),1632,'Whole three-sided actual caller hardware');eq(hw[:512],hw[1088:1600],'Entire hardware FX512 restoration');eq(hw[512:540],hw[1600:1628],'Entire hardware ENV28 restoration');counts['whole_caller_FX512_ENV28']+=1
     source_prefix=[];API_count=0;owned_byteflows=[]
     if has:
      prefix=stem+'MFC/';source_prefix=list(struct.iter_unpack('<IIQII',a.data(prefix+'refused/accesses.bin')));API_count=len(a.data(prefix+'refused/APIs.bin'))//352
      eq(len(a.data(prefix+'refused/APIs.bin')),API_count*352,'Complete typed API record vectors');entry_state=a.data(prefix+'entry/State.bin');entry_fx=a.data(prefix+'entry/FX.bin');entry_cpu=a.data(prefix+'entry/CPU.bin');memory={}
      for address,size in struct.iter_unpack('<2I',a.data(prefix+'entry/memory-index.bin')):memory[address]=a.data(prefix+f'entry/memory-{address}-{size}.bin');eq(len(memory[address]),size,'Whole actual own entry region')
      # Fill absent code/IAT inputs only from the fixed physical source image;
      # captured current entry values always win.
      supplemental={'memory':{}};extension.loader(supplemental)
      for address,data in supplemental['memory'].items():memory.setdefault(address,data)
      if mode in(7,8):
       _,derived=literal.derive(entry_state,entry_fx,entry_cpu,memory,p['inputs'],contracts);eq(source_prefix,[tuple(v)for v in derived['source_accesses'][:len(source_prefix)]],'Entire source-derived accepted/last-attempted causal prefix');eq(API_count,1,'One complete TLS source API before controlled store/transport denial')
      elif mode==11:
       I=literal.Literal;cpu=struct.unpack('<10I',entry_cpu);m=I(entry_state,entry_fx,entry_cpu,memory,program={r['pc']:r for r in contracts['instructions']},callbacks={});m.inputs=p['inputs'];m.initial_flags=cpu[8];m.call_stack.append((0x5ae3e4,cpu[4],0x410a80,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0))
       while m.cursor in m.program and len(m.accesses)<len(source_prefix):m.step()
       eq(source_prefix,m.accesses[:len(source_prefix)],'Literal mutated manager lazy-path accepted source prefix');eq(API_count,0,'No typed API admitted on unproved lazy path')
      else:eq(source_prefix,[],'Constructor/physical/segment refusal precedes literal operand admission');eq(API_count,0,'No source API entered before precise early refusal')
      # All complete capacity bytes come from this case's own entry, with only
      # source-proved committed writes. Mode7 final recorded write is an attempt
      # rejected by RO permission; mode8 API semantic CS transport is uncommitted.
      for owner in p['inputs']['role_owners']:
       expected=bytearray(memory[owner['new']]);end=source_prefix[:-1]if mode==7 else source_prefix
       for pc,address,value,width,writing in end:
        if writing and owner['new']<=address and address+width<=owner['new']+owner['extent']:expected[address-owner['new']:address-owner['new']+width]=value.to_bytes(width,'little')
       actual=a.data(prefix+f'refused/borrowed/{p["inputs"]["role_owners"].index(owner)}.bin');eq(bytes(expected),actual,'Whole borrowed capacity causal byteflow');owned_byteflows.append(dict(role=owner['role'],initial_hex=memory[owner['new']].hex(),source_refused_hex=bytes(expected).hex()));counts['whole_borrowed_capacity_prefixes']+=1
      if mode==7:need(source_prefix and source_prefix[-1][1:]==(0x33005014,0,1,1),'Actual last attempted byte14 RO write');counts['recorded_rejected_source_write_payloads']+=1
      # Fresh real provider export, whole CS40 sides and complete owned lifetime.
      virtual=(out/f'logical-{level}-{mode}').resolve();oldraw=V.raw
      def raw(path):
       q=Path(path).resolve();return a.data(prefix+q.relative_to(virtual).as_posix())if q.is_relative_to(virtual)else oldraw(q)
      V.raw=raw;context=a.words(prefix+'cleaned/resource-context.bin',12,'Q');eq(context[2:7],(0,0,0,0,0),'Native TLS/CS40 unheld and released');services=[];tls=None;assoc=0;section=None;depth=0;freed=False;deleted=False;thread=None
      try:
       for serial in range(context[11]):
        base=virtual/'resources'/str(serial);w=struct.unpack('<8Q',raw(base/'call.bin'));eq(w[:2],(1,serial),'Every actual live service contiguous');kind,arg0,arg1,result,tid,error=w[2:];thread=tid if thread is None else thread;eq(tid,thread,'One actual native current-thread owner');identity=V.native_identity(base,kind,proofs);before=raw(base/'CS-before40.bin');after=raw(base/'CS-after40.bin');eq((len(before),len(after)),(40,40),'Whole native CS40 service sides')
        if kind==0:need(tls is None and result!=0xffffffff,'Actual one owned TLS allocation');tls=result
        elif kind==1:eq(arg0,tls,'Exact owned TLS association slot');need(not freed and result==1,'Successful live TLS set');assoc=arg1
        elif kind==2:eq(arg0,tls,'Exact owned TLS lookup slot');need(not freed and result==assoc,'Actual current-thread TLS association')
        elif kind==3:eq(arg0,tls,'Exact TLS free slot');need(not freed and not assoc and result==1,'Actual clear before free');freed=True
        elif kind==4:need(section is None,'One owned native CS40 initialization');section=arg0;eq(V.cs(after),(0,0),'Native CS initialized unheld')
        elif kind in(5,6):eq(arg0,section,'Same actual live native CS40');need(not deleted,'Actual CS live');eq(V.cs(before),(depth,thread if depth else 0),'Incoming actual depth');depth+=1 if kind==5 else -1;need(depth in(0,1),'Finite actual balanced CS');eq(V.cs(after),(depth,thread if depth else 0),'Outgoing actual depth')
        elif kind==7:eq(arg0,section,'Same actual CS destruction');need(not deleted and not depth,'Unheld destruction');deleted=True
        else:raise ValueError('Unexpected service on refused finite prefix')
        services.append(dict(words=w,CS_before_hex=before.hex(),CS_after_hex=after.hex()));identities.append(dict(level=level,mode=mode,serial=serial,kind=kind,call_words=w,proof_identity=[kind,identity['actual_owner'],identity['RVA'],identity['entry64']]));counts['actual_API_identity_CS40_sides']+=2
       need(freed and deleted and not depth,'Every actual owned resource released after denial');counts['actual_owned_lifecycles']+=1
      finally:V.raw=oldraw
     else:need(not any(k.startswith(stem+'MFC/resources/')for k in a.entries),'Early constructor refusal created no owned native resource');counts['pre_resource_refusals']+=1
     cases.append(dict(level=level,mode=mode,terminal=list(terminal),reason=reason,source_access_prefix=source_prefix,source_API_records=API_count,borrowed_byteflows=owned_byteflows,complete_private_retry_compared=True,attempted_mutation_source_authored=True,rejected_local_read_payload_observed=False,recorded_failed_write_payload=(list(source_prefix[-1])if mode==7 else None)))
     counts['actual_unchanged_poisoned_retries']+=1
   finally:a.close();a.entries.clear();a.bundles.clear();del a;closed=True
  eq(counts['actual_precise_denials'],24,'All24 actual precise current denials');eq(counts['actual_unchanged_poisoned_retries'],24,'All24 full captured retries');eq(counts['whole_caller_FX512_ENV28'],48,'Every denial/retry complete actual caller')
  for filename,value in [('causal-controls.json',cases),('actual-provider-identity-joins.json',identities),('unique-physical-API-proofs.json',list(proofs.values()))]:q=out/filename;q.write_text(json.dumps(value,indent=2)+'\n');pin(q)
  for q,h in V.PINS.items():pin(q,h)
  pin(__file__);pin(sys.executable)
  for q,h in pins.items():eq(sha(q),h,'Every physical input stable after closure')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'report.json').write_text(json.dumps(dict(passed=passed,execution=str(execution),execution_sha256=digest,scope='Current24 connected precise public denials, source-derived accepted prefixes/fullborrowed capacities, entire captured State/CPU/FX/pages/routes/private retry vectors, actual native provider exports/lifetimes and full caller512/28; rejected reads remain unobserved',counts=dict(counts),files=pins,all_bounded_readers_closed=closed,whole_Runtime_hidden_private_retry_claim=False,whole_old_registry_private_retry_claim=False,whole_permissions_retry_claim=False,initializer_credit=0),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])

"""Independent bounded review of the singleton initialization representation relation.

This checks genuine archives, physical literal bytes and a separate conservative
object-alias CFG pass. It does not interpret pseudocode as an execution oracle.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact independent policy dependency '+str(p));PINS[str(p)]=v;return p
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def w(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def aliases(function):
 """Track this-object aliases over every literal insertion-method CFG edge.

Heap element pointers are deliberately unknown after a member load. External
new/delete calls kill volatile registers and must receive no object alias. Only
literal accesses whose base still denotes the object are approved as members.
"""
 rows={r['pc']:r for r in function['instructions']};work=[(function['entry'],0,{'ECX'},frozenset())];seen=set();members=set();calls=set();visits=0
 def memory(text,sp,regs,slots):
  match=re.search(r'\[([A-Z]+)(?: \+ (?:0x([0-9a-f]+)|-0x([0-9a-f]+)))?\]',text)
  if not match:return None
  base,pos,neg=match.groups();off=int(pos or neg or'0',16)*(-1 if neg else 1)
  if base=='ESP':return ('stack',sp+off)
  if base in regs:return ('object',off)
  return ('unknown',off)
 while work:
  pc,sp,regs,slots=work.pop();key=(pc,sp,frozenset(regs),slots)
  if key in seen:continue
  seen.add(key);need(pc in rows,'Complete literal insertion CFG');r=rows[pc];visits+=1;need(visits<20000,'Finite independent alias fixed point')
  text=r['text'];op,_,operands=text.partition(' ');parts=operands.split(',');fall=pc+len(bytes.fromhex(r['bytes_hex']));regs=set(regs);slots=set(slots)
  for part in parts:
   loc=memory(part,sp,regs,slots)
   if loc and loc[0]=='object':need(loc[1]in(4,8,12),'No insertion method read/write of object byte0');members.add((pc,loc[1]))
  if op=='MOV':
   dest,source=parts;loc=memory(source,sp,regs,slots);alias=source in regs or(loc and loc[0]=='stack'and loc[1]in slots)
   if dest in ('EAX','ECX','EDX','EBX','ESI','EDI','EBP'):
    regs.discard(dest)
    if alias:regs.add(dest)
   else:
    destloc=memory(dest,sp,regs,slots)
    if destloc and destloc[0]=='stack':
     slots.discard(destloc[1])
     if alias:slots.add(destloc[1])
    elif alias:raise ValueError('Object alias must not escape the bounded insertion method')
  elif op=='PUSH':
   loc=memory(parts[0],sp,regs,slots);alias=parts[0]in regs or(loc and loc[0]=='stack'and loc[1]in slots);sp-=4;slots.discard(sp)
   if alias:slots.add(sp)
  elif op=='POP':
   regs.discard(parts[0])
   if sp in slots:regs.add(parts[0])
   slots.discard(sp);sp+=4
  elif op in ('SUB','ADD')and parts[0]=='ESP':sp+=(1 if op=='ADD'else-1)*int(parts[1],16)
  elif op=='CALL':
   target=int(parts[0],16);need(target in(0x5abd26,0x5abd1a),'Only literal external new/delete calls');need(sp not in slots,'No this-object alias passed as allocation count or free pointer');calls.add((pc,target))
   regs.difference_update(('EAX','ECX','EDX'))
  elif op not in ('CMP','TEST') and op not in ('RET','JMP') and not op.startswith('J'):
   # Any arithmetic destination loses a precise object-base identity. The
   # literal method never reconstructs this by arithmetic; spill reloads do.
   if parts[0]in regs:raise ValueError('Unreviewed arithmetic on object alias '+text)
  if op=='RET':continue
  if op=='JMP' or op.startswith('J'):
   target=int(parts[0],16);work.append((target,sp,regs,frozenset(slots)))
   if op=='JMP':continue
  work.append((fall,sp,regs,frozenset(slots)))
 return dict(CFG_states=len(seen),physical_instructions=len(rows),object_member_accesses=sorted(members),external_calls=sorted(calls),object_byte0_accesses=0)
def main(name):
 out=ROOT/'reports/m4-onexit-review'/name;need(not out.exists(),'Fresh independent policy receipt');out.mkdir(parents=True);passed=False;counts=collections.Counter();rows=[]
 try:
  paired=json.loads(pin(ROOT/'reports/m4-onexit-source/paired-initialization-policy-r3/report.json','29153950456a890bc306a5d4c1aff2f5b0d3c1e9165dcb34ea2cbeee5f99b83a').read_bytes());need(paired['passed']and not paired['blanket_page_mask']and not paired['whole_game_liveness_proven'],'Exact bounded source policy')
  for p,h in paired['files'].items():pin(p,h)
  old=json.loads(pin(ROOT/'reports/m4-onexit-review/liveness-review-r1/report.json','6ed6bcb4cb55c6c1d4497a2ea560041b5cdf8b6e405276eb34be6fec73efa945').read_bytes());need(old['passed'],'Previously preserved genuine consumer counterexample')
  pin(ROOT/'reports/m4-onexit-review/liveness-native-supplement-r1/report.json','0851d0d8cb05c36f87aacfc3fa7794d9174c43c3c91b84301a9f217209b83e2c')
  field=json.loads(pin(ROOT/'reports/m4-onexit-source/field-analysis-r1/report.json','bd127e908fe3056a986f3977e35e86bd1084086fb92a5e997bc36c49bdd9dfa0').read_bytes());need(field['passed']and not field['whole_game_liveness_proven'],'Narrow static consumer gate')
  for p,h in field['files'].items():pin(p,h)
  PE=load('independent_field_PE',ROOT/'tools/analysis/pe.py');raw=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(raw)
  static=json.loads(pin(ROOT/'reports/m4-onexit-source/field-reference-r2/export.json').read_bytes());need(static['target_sha256']==sha(ROOT/'MW3/Mech3.exe'),'Static export exact target')
  functions={f['entry']:f for f in static['exports']}
  for f in functions.values():
   for r in f['instructions']:
    code=bytes.fromhex(r['bytes_hex']);offset,_=pe.rva_range(r['pc']-pe.image_base,len(code));need(raw[offset:offset+len(code)]==code,'Every consumer instruction has literal PE bytes');counts['physical_consumer_instructions']+=1
  offset,_=pe.rva_range(0x49d5d0-pe.image_base,10);need(raw[offset:offset+10]==bytes.fromhex('518a442403a2e8996000'),'Exact PUSH ECX/local highbyte singleton store')
  alias=aliases(functions[0x49da10]);need(len(alias['object_member_accesses'])==18,'Complete separately derived insertion member accesses')
  D=load('independent_paired_capture',ROOT/'tools/m4-crt-allocation-root/run_v2.py');original=json.loads(pin(ROOT/'reports/m4-onexit-source/original-run-r5/report.json','dbf50bb8d64645565b7b1f7ff6a622eae4257cb8fae5a188a06cb329b907143a').read_bytes());ori=D.DirectSet(Path(original['original_capture']),pin)
  page_index=22;field_offset=0x9e8
  try:
   for level in('O0','O2'):
    native=D.DirectSet(ROOT/f'reports/m4-joint-startup54-root/execution-r6/{level}/transport.json',pin)
    try:
     for seq in range(6):
      a=ori.data(f'phase/{seq}/26.bin');b=native.data(f'sequence-{seq}/phase-26.bin');spi=ori.data(f'phase/{seq}/25.bin');need(w(a,16)[0]==w(b,16)[0]==0x49d5c0,'Genuine constructor association')
      need(w(spi,80)[0]==w(a,40)[0],'Genuine original SPI return carried to constructor BEFORE');original_derived=w(a,40)[0]>>24;native_derived=w(b,40)[0]>>24
      ao=a[121060+page_index*4096+field_offset];bo=native.data(f'sequence-{seq}/phase-26-after-page-{0x609000}.bin')[field_offset];need(ao==original_derived and bo==native_derived,'Independent own-BEFORE literal singleton derivation');counts['own_BEFORE_derivations']+=2
      for phase in range(26,54):
       x=ori.data(f'phase/{seq}/{phase}.bin')
       for side,base in(('after',121060),('before',2276)):
        if phase==26 and side=='before':continue
        y=native.data(f'sequence-{seq}/phase-{phase}-{side}-page-{0x609000}.bin');need(x[base+page_index*4096+field_offset]==original_derived and y[field_offset]==native_derived,'Exact each-branch singleton carry without replacement');counts['raw_branch_carry_checks']+=2
      rows.append(dict(level=level,sequence=seq,original_BEFORE_ECX=w(a,40)[0],native_BEFORE_ECX=w(b,40)[0],original_raw_singleton=ao,native_raw_singleton=bo,original_native_equal=ao==bo))
    finally:native.close()
  finally:ori.close()
  observations=json.loads(pin(ROOT/'reports/m4-onexit-source/paired-initialization-policy-r3/paired-observations.json').read_bytes());need(len(observations)==648,'Every raw paired phase retained')
  iat_addresses={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc}
  for observation in observations:
   need(len(observation['nonstack_pages'])==56,'Both entire28 nonstack page observations retained')
   for page in observation['nonstack_pages']:
    allowed=set()
    if page['page']==0x5bb000:
     for address in iat_addresses:allowed.update(range(address&4095,(address&4095)+4))
    if page['page']==0x609000 and(observation['phase']>26 or observation['phase']==26 and page['side']=='after'):allowed.add(0x9e8)
    need(all(d['offset']in allowed for d in page['differences']),'No wider byte relation or blanket masking');counts['retained_whole_page_difference_inventory']+=1
   for side in('before','after'):
    eo=bytes.fromhex(observation[f'ENV_{side}_original_hex']);en=bytes.fromhex(observation[f'ENV_{side}_native_hex']);need(eo[:12]==en[:12],'Exact raw legacy x87 ENV head')
    if observation['phase']not in((25,26,27)if side=='after'else(26,27,28)):need(eo==en,'ENV differences only on finite actual SPI metadata interval')
  pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'actual-field-derivations.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'actual-field-derivations.json')
  report=dict(passed=passed,scope='Independent review of bounded selected54 initialization representation relation, preserving earlier genuine SPI/constructor consumer counterexample and all unequal raw bytes',counts=dict(counts),insertion_alias_CFG=locals().get('alias'),source_singleton_values_hardcoded=False,candidate_or_original_bytes_edited=False,whole_page_mask=False,raw_pair_equality_claimed=False,full_original_stack_equivalence_claimed=False,whole_game_dynamic_alias_liveness_proven=False,known_UI_container_consumer_scope='Literal exact225-instruction insertion method tracks all this aliases through CFG/spills, only members+4/+8/+12 accessed; exact49D600 cleanup accesses those members; direct-address inventory bounded to persisted exports. Unknown dynamic aliases remain excluded.',acceptance_recommendation='Admit the explicit selected-initialization data contract only when strict native persistent source/ownership/fault-control gates also pass. Do not reuse the discarded13-root no-consumer claim or infer exact original/native machine/whole-game equivalence.',initializer_credit=False,files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])

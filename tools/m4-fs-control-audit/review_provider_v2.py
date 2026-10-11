"""Read-only review of frozen109 source observer and actual next-growth leaves."""
from pathlib import Path
import difflib,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=R/'reports/m4-fs-control-audit'/name;need(not out.exists(),'Fresh independent provider review');out.mkdir();pins={};facts=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=pins.get(str(p))
  if v is None:v=sha(p)
  need(h is None or h==v,'Frozen source/capture '+str(p));pins[str(p)]=v;return p
 source=json.loads(pin(R/'reports/m4-fs-provider-review/source-r1/report.json','f151ee977a744a3d19a39c24ad16d0e957565ffb1fdd713865a41b77e94b3fe0').read_bytes());need(source['passed'],'Actual final complete provider proof')
 scripts={}
 for p in('observe109_v3.py','observe109_v2.py','final_observer109_v3.py','final_observer109_v2.py','exact_equal.py','derive.py','derive_v2.py'):
  path=R/'tools/m4-fs-provider-review'/p;scripts[p]=pin(path,source['files'].get(str(path))).read_text()
 before=scripts['final_observer109_v2.py'];after=scripts['final_observer109_v3.py'];diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='cached-capacity-v2',tofile='genuine-first-msize-v3'));(out/'growth-source.diff').write_text(diff);pin(out/'growth-source.diff')
 equality=load('review_complete_byte_equality',R/'tools/m4-fs-provider-review/exact_equal.py');tests=equality.selfcheck();need(tests==dict(equal_cases=4,difference_refusals=6),'Complete equality helper tests')
 for n in(0,1,3,4096,8192):
  b=bytes((i*37+19)&255 for i in range(n));equality.equal(b,bytearray(b),'Same full bytes')
  for other in(b+b'x',b[:-1]if n else b'x',b[:n//2]+bytes([b[n//2]^1])+b[n//2+1:]if n else b'x'):
   try:equality.equal(b,other,'Strict complete byte/extent failure')
   except ValueError:pass
   else:raise ValueError('Unequal whole byte relation accepted')
 need("if len(a)==len(b)and a==b:return"in scripts['exact_equal.py']and scripts['exact_equal.py'].index('if len(a)==len(b)and a==b:return')<scripts['exact_equal.py'].index('differences=[]'),'Full len+byte equality precedes diagnostic-only difference enumeration')
 need("while len(responses.growth)==initial_growths:"in after and "m.invoke_external(0x410210,0xffffffa0,responses)"in after and "capacity_steps=(first_query_capacity-initial_used)//4+1"in after,'Literal source loop retained; DWORD arithmetic count derived only from genuine first source query')
 need("responses.facts[first_API:responses.index]"in after and "if f['name']=='HeapSize'"in after and "first_query_capacity=queries[0]['words'][17]"in after,'Finite actual first-query result is sole capacity input after its checked typed call')
 need("need(n==observed_replays==capacity_steps and len(responses.growth)==initial_growths+1"in after,'Actual replay count is only final comparison; it cannot steer source replay')
 loop=after[after.index('initial_used='):after.index('grown_count=')];need('observed_replays'not in loop[:loop.index('need(n==observed_replays')],'No actual AFTER replay count drives loop')
 need('first_query_capacity'not in before and before[:before.index('  capacity_steps=')]==after[:after.index('  initial_used=')]and before[before.index('  grown_count='):]==after[after.index('  grown_count='):],'Growth repair changes only capacity derivation/comparison, not source body/checkpoint/cleanup semantics')
 observer=scripts['observe109_v3.py'];need(observer.count('machine,responses=B.bootstrap(')==1 and "per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False"in observer,'One true bootstrap per sequence and explicit bounded numerical policy')
 need("remaining==['registry-bootstrap-before']"in after and "responses.complete()"in after and "for owner in ordered:"in after,'All source checkpoints/actual APIs and genuine original frees remain exhausted/checked')
 need("m.call_stack[-1]=(0x5f401ea0,)+frame[1:]"in after,'Thunk metadata projection changes entry name only; true source frame and machine retained')
 need("(self.root,pc,size,w[2],w[4],address-w[16],True)in self.fs_allowed"in after,'Shared writes keep exact prior-owner root/CALL/PC/requested offset checks')
 responses=pin(R/'tools/m4-onexit-review/provider_responses.py',source['files'][str(R/'tools/m4-onexit-review/provider_responses.py')]).read_text()
 for phrase in("tuple(w[2:8])==(site,c['slot'],c['raw'],frame,ret,c['argc'])","tuple(w[20:20+c['argc']])==args","allocation['native']==w[16]","I.need(result==w[17]","allocation.update(guest=guest,requested=requested,extent=rounded,capacity=0","requested==capacity+16"):
  need(phrase in responses,'Independent actual typed frame/result/owner leaf relation retained '+phrase)
 # Corroborate the literal unsigned compare and one-DWORD append in source-only contracts.
 contracts=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json').read_bytes())['instructions'];selected=[r for r in contracts if 0x78002fe5<=r['pc']<0x78003041 or 0x7801e27b<=r['pc']<0x7801e2c0]
 need(any(r['pc']==0x78003002 and r['mnemonic']=='cmp'and r['operands']=='eax, edx'for r in selected)and any(r['pc']==0x78003004 and r['mnemonic']=='jbe'and r['operands']=='0x7800301d'for r in selected),'Literal original callback capacity branches to growth when measured unsigned capacity is less than or equal to used bytes')
 need(any(r['mnemonic']=='add'and r['operands'].endswith(', 0x4')for r in selected),'Literal callback vector advances by one DWORD')
 pcjson=[dict(pc=r['pc'],mnemonic=r['mnemonic'],operands=r['operands'],bytes_hex=r['bytes_hex'])for r in selected];(out/'literal-growth-rows.json').write_text(json.dumps(pcjson,indent=2)+'\n');pin(out/'literal-growth-rows.json')
 for level in('O0','O2'):
  manifest=pin(R/'reports/m4-joint-startup109-root/execution-r3'/level/'transport.json');value=json.loads(manifest.read_bytes());wanted={}
  for seq in range(6):
   wanted[f'sequence-{seq}/selected/registry-summary.bin']=(seq,'selected');wanted[f'sequence-{seq}/selected/locale-allocations.bin']=(seq,'allocations');wanted[f'sequence-{seq}/cleaned/locale-api-336-witness.bin']=(seq,'first_msize');wanted[f'sequence-{seq}/growth-replay-count.bin']=(seq,'replays')
  got={}
  for part in value['parts']:
   path=pin(manifest.parent/part['bundle'],part['sha256'])
   with CaptureBundle(path,part['sha256'])as bundle:
    names=set(bundle.names())
    for logical,(seq,kind)in wanted.items():
     if logical in names:
      need((seq,kind)not in got,'One immutable actual scalar observation');got[seq,kind]=bundle.read_bytes(logical)
   print(json.dumps(dict(level=level,authenticated_part=part['bundle'],scalar_records=len(got))),flush=True)
  need(len(got)==24,'All12 actual bounded scalar/owner sequences across both levels')
  for seq in range(6):
   q=struct.unpack('<32Q',got[seq,'selected']);a=list(struct.iter_unpack('<16Q',got[seq,'allocations']));w=struct.unpack('<32Q',got[seq,'first_msize']);observed=struct.unpack('<I',got[seq,'replays'])[0];used=q[7]-q[6];owner=next(p for p in a if p[1]==q[6]and p[8]);capacity=w[17]
   need(q[5]==q[9]==81 and used==324 and q[8]==0,'Computed selected callbacks/used bytes retained with legitimate cached capacity0 after genuine realloc')
   need(w[1:5]==(336,0x780015b5,0x7802e1dc,0x34bd0)and w[7]==3 and w[8]==w[12]==capacity==336 and w[14:16]==(1,1),'Genuine actual typed first HeapSize leaf supplies exact scalar result')
   need(w[20:23]==(0x48450001,0,q[6])and w[16]==owner[7]==owner[8]>0xffffffff and w[13]==capacity and owner[3]<=capacity<=owner[4],'Exact owned HANDLE token/flags/whole guest+full native pointer/current measured extent')
   expected=(capacity-used)//4+1;need(observed==expected==4,'First actual leaf capacity independently determines exact next-growth call count')
   facts.append(dict(level=level,sequence=seq,selected_used_bytes=used,cached_capacity=q[8],actual_first_source_msize_capacity=capacity,predicted_replays=expected,actual_replays=observed,first_API_index=w[1],full_native=owner[8]))
 need(source['provider_counts']['complete109_provider_sequences']==12 and source['provider_counts']['whole_State_checkpoints']==20196 and source['provider_counts']['actual_heap_destroys']==source['provider_counts']['actual_post_HeapDestroy_identity_proofs']==12,'Final actual proof has all12 complete source/growth/cleanup/physical postdestroy sequences')
 pin(__file__);report=dict(passed=True,scope='Independent read-only frozen observer/derivation review plus narrow actual raw scalar extraction. Actual source-r1 complete prediction remains separate whole source proof; no execution or new initializer credit here. Capacity is a genuine typed first source HeapSize leaf output, not cached zero or AFTER machine seed. Full literal replay/CALL/frame/API/growth/cleanup/checkpoints unchanged. Whole exact equality remains length plus every byte. Accepted finite old numerical oracles and source/native branch scopes remain explicit.',comparison_semantics_unchanged=True,growth_uses_genuine_first_source_msize=True,growth_has_no_AFTER_seed=True,source_growth_cleanup_unchanged=True,actual_scalar_sequences=12,facts=facts,exact_equality_tests=dict(equal_cases=9,difference_refusals=21),callback_execution=False,initializer_credit=0,files=pins,current_physical_closure=verify_manifest(pins))
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])

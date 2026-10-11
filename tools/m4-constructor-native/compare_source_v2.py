"""Prepared branch-specific source comparison; exporter admission is separate."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_derivation_v2',R/'tools/m4-constructor-native/derive_source_v2.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def region(memory,address,n):
 matches=[(int(a),bytes.fromhex(b))for a,b in memory.items()if int(a)<=address and address+n<=int(a)+len(bytes.fromhex(b))];need(len(matches)==1,'One complete source endpoint region');a,b=matches[0];return b[address-a:address-a+n]
def main(manifest,digest,preparation,prep_digest,name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh source gate');out.mkdir();files={};passed=False;rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip')and p.name not in('payload.bin','index.json','transport.json'),'Loose inputs only, no archive/facade reader');d=sha(p);need(h is None or h==d,'Exact admitted loose input');files[str(p)]=d;return p
 try:
  receipt=json.loads(pin(manifest,digest).read_bytes());prep=json.loads(pin(preparation,prep_digest).read_bytes());need(receipt['passed']and receipt['original_or_native_input_export_only']and not receipt['source_AFTER_seed']and prep['passed'],'Exact finite BEFORE-only input admission')
  for rec in(receipt,prep):
   for p,h in rec['files'].items():pin(p,h)
  cases=receipt['cases'];need(len(cases)in(18,36,54),'Complete six-domain original/native case extent')
  seen=set()
  for case in cases:
   inp=json.loads(pin(case['input_path'],case['input_sha256']).read_bytes());need(not any(k.startswith('AFTER')or k=='expected'for k in inp),'Source input has no candidate/original equality target')
   key=(inp['branch'],case['sequence'],inp['root']);need(key not in seen,'One source execution per branch/domain/root');seen.add(key)
   result=D.derive(inp,preparation)
   # Only after execution has terminated may an equality target be opened.
   target=json.loads(pin(case['endpoint_path'],case['endpoint_sha256']).read_bytes());need(target['branch']==inp['branch'],'Separate input/equality target branch')
   actual=result['source_computed_CPU'];wanted=target['CPU'];need(len(wanted)==10 and all(actual[i]==wanted[i]for i in range(10)if i!=8),'Complete whole source-defined CPU registers/PC')
   if inp['branch']=='original':
    need('State_hex'not in target and target['original_State_observed']is False,'No original Remill State endpoint invented')
    mask=sum(1<<D.M.BITS[f]for f in result['source_remaining_undefined_flags']);need(((actual[8]^wanted[8])&~mask)==0,'Every currently defined architectural EFLAGS bit')
    need(inp['BEFORE_ENV28_hex']==target['ENV28_hex'],'Whole integer-only original ENV28 endpoint')
   else:
    need(result['source_computed_State_hex']==target['State_hex']and actual[8]==wanted[8],'Whole native literal State3504 and callback-defined CPU flags')
   need(result['source_computed_FX_hex']==target['FX_hex'],'Whole source-carried FX512 endpoint')
   endpoint_keys=set();page_count=owner_count=0
   for r in target['regions']:
    key=(r['address'],r['bytes']);need(key not in endpoint_keys and r['bytes']>0,'Distinct complete declared endpoint extents');endpoint_keys.add(key);raw=region(result['source_computed_memory'],*key);need(raw.hex()==r['hex'],'Every complete observed endpoint region '+hex(r['address']))
    if r['kind']=='whole-source-page':need(r['bytes']==4096 and r['address']%4096==0,'Whole source page geometry');page_count+=1
    elif r['kind']=='actual-owner-extent':owner_count+=1
    else:need(r['kind']in('source-stack','true-source-TIB','source-observed-field'),'Explicit finite source endpoint role')
   need(page_count==target['complete_source_page_count']and owner_count==target['complete_owner_extent_count'],'Declared full page/owner endpoint coverage, no implicit scope reduction')
   if 'accesses'in target:need([list(v)for v in result['accesses']]==target['accesses'],'All ordered source-defined operands')
   rows.append(result)
  for branch in {k[0]for k in seen}:need({(seq,root)for b,seq,root in seen if b==branch}=={(seq,root)for seq in range(6)for root in D.M.ROOTS},'Every actual current domain/root covered')
  q=out/'source-derivations.json';q.write_text(json.dumps(rows,indent=2)+'\n');pin(q);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p,h in list(files.items()):need(sha(p)==h,'Loose source input/equality target conservation')
  for p in(__file__,R/'tools/m4-constructor-native/derive_source_v2.py',R/'tools/m4-constructor-native/game_model_v2.py'):pin(p)
  d=dict(passed=passed,scope='Complete prepared constructor own-BEFORE literal gate with explicit original/native architecture scope',input_manifest_sha256=digest,preparation_sha256=prep_digest,cases=len(rows),original_State_equality_claim=False,unexplained_stack_difference_allowed=False,source_AFTER_seed=False,initializer_credit=0,reader_closed=True,files=files)
  q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),cases=len(rows))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])

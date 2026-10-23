"""Finite literal54 source-owned structural pairing, no archive readers."""
from pathlib import Path
import json,hashlib,struct,sys,traceback
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};cases=[];passed=False;frontier={}
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 def get(p):return json.loads(pin(p).read_bytes())
 try:
  for rel,h,n in [('constructor-original18-source-r4','48cad330f7fe559721fe10748efdf4261e92d22653ba141883065c4c9342fff6',18),('constructor-native36-source-r6','e7bc628fe59f20e69a5823e2f54ad88af94d9f0dbbfea1c51d8e45807d5c4392',36),('constructor-source-dependency-review-r8','4c91796493b1a91d9df78f3221fb53d146d9990da9edee4454d779adc3473755',None)]:
   p=pin(R/'reports/m4-138-validation-review'/rel/'report.json',h);rec=json.loads(p.read_bytes());assert rec['passed'];assert n is None or len(rec['cases'])==n
  for seq in range(6):
   for root in(0x4103f0,0x410440,0x459b40):
    base=R/'reports/m4-138-validation-review';a=get(base/f'constructor-original18-source-r4/original-{seq}-{root}/source-derivation.json')
    for level in('O0','O2'):
     frontier=dict(sequence=seq,root=root,branch=level);b=get(base/f'constructor-native36-source-r6/{level}-{seq}-{root}/source-derivation.json');ain=get(base/f'constructor-original18-source-r4/original-{seq}-{root}/input.json');binp=get(base/f'constructor-native36-source-r6/{level}-{seq}-{root}/input.json')
     def calls(result,inp):
      api={(f['site'],f['target']):name for f,name in zip(inp['APIs'],('HeapAlloc','HeapAlloc','EnterCriticalSection','HeapSize','LeaveCriticalSection'))};assert len(inp['APIs'])==5
      return [[site,['typed_API',api[(site,target)]]if(site,target)in api else ['source',target],ret]for site,target,ret in result['calls']]
     assert a['PCs']==b['PCs']and calls(a,ain)==calls(b,binp)and a['returns']==b['returns'];assert a['constructor_flag_consumers']==b['constructor_flag_consumers'];assert a['source_API_inputs']==b['source_API_inputs']==5
     aa=sorted(a['source_complete_owners'],key=lambda o:o['generation']);bb=sorted(b['source_complete_owners'],key=lambda o:o['generation']);assert len({o['generation']for o in aa})==len(aa)and len({o['generation']for o in bb})==len(bb);assert len({y['generation']-x['generation']for x,y in zip(aa,bb)})==1;assert len(aa)==len(bb);assert all(x.get('live',True)and y.get('live',True)for x,y in zip(aa,bb))
     def value(v,owners):
      found=[(i,v-o['guest'])for i,o in enumerate(owners)if o['guest']<=v<o['guest']+o['extent']];assert len(found)<=1;return ['owner',*found[0]]if found else ['literal',v]
     def words(raw,owners):assert len(raw)%4==0;return [value(v,owners)for v in struct.unpack('<'+'I'*(len(raw)//4),raw)]
     firsta=get(base/f'constructor-original18-source-r4/original-{seq}-4260848/input.json');firstb=get(base/f'constructor-native36-source-r6/{level}-{seq}-4260848/input.json')
     for current,first in((aa,firsta),(bb,firstb)):
      initial_roles=sorted(first['owners'],key=lambda o:o['generation']);assert len(initial_roles)==8
      for i in range(1,8):
       own=initial_roles[i];assert struct.unpack_from('<2I',bytes.fromhex(own['initial_hex']))==(own['guest'],own['guest']);assert current[i]['guest']==own['guest']and current[i]['generation']==own['generation'];assert bytes.fromhex(current[i]['initial_hex'])[8:12]==bytes.fromhex(own['initial_hex'])[8:12]
     original_births={}
     for earlier_root in (0x4103f0,0x410440,0x459b40):
      earlier=get(base/f'constructor-original18-source-r4/original-{seq}-{earlier_root}/source-derivation.json')
      for owner in earlier['source_complete_owners']:
       if 'source_requested'in owner:
        key=(owner['guest'],owner['generation']);size=owner['source_requested'];assert key not in original_births or original_births[key]==size;original_births[key]=size
      if earlier_root==root:break
     owner_rows=[]
     for i,(x,y)in enumerate(zip(aa,bb)):
      assert x['extent']==y['extent'];request=y['requested']
      if i>7 and (x['guest'],x['generation'])not in original_births:
       owner_rows.append(dict(role=i,actual_extent=x['extent'],whole_branch_backings_independently_validated=True,semantic_pair_claim=False,reason='Carried birth belongs to intervening nonconstructor source root; logical original allocation input is outside literal18 scope'));continue
      assert request in(4,12,128)
      # Existing original graph backings are observed at rounded API size16;
      # logical node extent12 is independently traversed/validated source graph.
      assert x['requested']==request or (x['requested']==16 and 'source_requested'not in x and ((1<=i<=7 and request==12)or original_births.get((x['guest'],x['generation']))==request))
      compare_bytes=request;sentinel_payload_unread=False
      if request==12 and all(bytes.fromhex(owner['initial_hex'])[8:12]==bytes.fromhex(owner['source_final_hex'])[8:12]and not any(address<owner['guest']+12 and address+width>owner['guest']+8 for pc,address,val,width,write in result['accesses'])for result,owner in((a,x),(b,y))):
       for result,owner in((a,x),(b,y)):
        initial=bytes.fromhex(owner['initial_hex']);final=bytes.fromhex(owner['source_final_hex']);assert initial[8:12]==final[8:12]
        assert not any(address<owner['guest']+12 and address+width>owner['guest']+8 for pc,address,val,width,write in result['accesses'])
       compare_bytes=8;sentinel_payload_unread=True
      assert words(bytes.fromhex(x['source_final_hex'])[:compare_bytes],aa)==words(bytes.fromhex(y['source_final_hex'])[:compare_bytes],bb)
      owner_rows.append(dict(role=i,logical_bytes=request,paired_semantic_bytes=compare_bytes,own_unread_sentinel_payload_preserved=sentinel_payload_unread,actual_extent=x['extent'],branch_tails_independently_conserved=True))
     def writes(result,owners):return [dict(PC=w['PC'],address=value(w['address'],owners),width=w['width'],value=value(w['value'],owners),owner=value(w['owner'],owners),source_access_index=w['source_access_index'])for w in result['constructor_owned_writes']]
     assert writes(a,aa)==writes(b,bb)
     def fs(result):
      events=result['constructor_FS'];entry=events[0]['head']
      def norm(v):return 'own-entry-head'if v==entry else v
      rows=[]
      for e in events:
       q={k:v for k,v in e.items()if k not in('head','previous','raw12_hex')}
       for k in('head','previous'):
        if k in e:q[k]=norm(e[k])
       if 'raw12_hex'in e:
        first,handler,index=struct.unpack('<3I',bytes.fromhex(e['raw12_hex']));q['raw12']=[norm(first),handler,index]
       rows.append(q)
      return rows
     assert fs(a)==fs(b)
     # Whole source-computed constructor global output page after typed owner addresses.
     page=0x5f2000;assert words(bytes.fromhex(a['source_computed_memory'][str(page)]),aa)==words(bytes.fromhex(b['source_computed_memory'][str(page)]),bb)
     cases.append(dict(**frontier,exact_literal_PC_call_return_path=True,exact_flag_consumers=True,whole_typed_global5F2000=True,whole_source_logical_owner_fields=owner_rows,exact_source_owned_writes=len(a['constructor_owned_writes']),exact_balanced_FS_events=len(a['constructor_FS']),source_API_occurrences=5,original_whole_State_claim=False))
  assert len(cases)==36;passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc())
 finally:
  pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='36 original18/native36 literal structural joins after independent entire endpoint validation; exact unique chronological generation-role bijection, exact source paths/writes/FS records and full typed5F2000 output. Does not equate untouched sentinel payloads, uninitialized branch allocation tails, opaque Win32 CS internals, or extra carried logical fields born outside constructor18 source scope. Every excluded whole backing remains independently branch-validated; every constructor source-owned write is paired.',cases=cases,frontier=frontier,initializer_credit=0,source_AFTER_seed=False,canonical_reader_opened=False,native_input_carry_policy_review_pending=True,complete_constructor_acceptance_gate=False,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])

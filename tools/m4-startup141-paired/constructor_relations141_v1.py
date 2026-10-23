"""Pure current141 constructor structural relation, all retained v9 rules.

No IO/model/eval; complete original/current native endpoint admissions are
caller prerequisites. Unread sentinel payloads retain exact own source carry;
unmodeled intervening-owner fields never gain a new crossbranch equality claim.
"""
import struct

def compare(seq,root,level,a,b,ain,binp,firsta,firstb,earlier_original_derivations,original_endpoint,native_endpoint,native_carried):
 assert type(seq)is int and 0<=seq<6 and root in(0x4103f0,0x410440,0x459b40)and level in('O0','O2')
 assert a['root']==b['root']==ain['root']==binp['root']==root and a['branch']==ain['branch']=='original'and b['branch']==binp['branch']==level
 assert a['source_AFTER_seed']is False and b['source_AFTER_seed']is False and ain['source_AFTER_seed']is False and binp['source_AFTER_seed']is False
 assert original_endpoint['sequence']==native_endpoint['sequence']==native_carried['sequence']==seq and original_endpoint['root']==native_endpoint['root']==native_carried['root']==root
 assert all(original_endpoint[k]is True for k in('source_complete','whole_GPR_EIP','defined_EFLAGS','whole_FX512','whole_ENV28'))and original_endpoint['source_AFTER_seed']is False
 assert native_endpoint['whole_own_CPU40']is True and native_endpoint['defined_EFLAGS']is True and native_endpoint['whole_own_State3504']is True and native_endpoint['whole_own_FX512']is True and native_endpoint['whole_own_ENV28']is True and native_endpoint['whole_own_pages_and_backings']is True and native_endpoint['source_AFTER_seed']is False
 assert native_carried['level']==level and native_carried['phase']=={0x4103f0:13,0x410440:14,0x459b40:39}[root]and native_carried['AFTER_seed']is False and native_carried['source_seed']is False and native_carried['whole_native_component_journals_compared']is True and native_carried['whole_native_State_CPU_FX_compared']is True
 assert firsta['root']==firstb['root']==0x4103f0 and firsta['branch']=='original'and firstb['branch']==level
 assert set(earlier_original_derivations)==set((0x4103f0,0x410440,0x459b40)[:(0x4103f0,0x410440,0x459b40).index(root)+1])
 def calls(result,inp):
  api={(f['site'],f['target']):name for f,name in zip(inp['APIs'],('HeapAlloc','HeapAlloc','EnterCriticalSection','HeapSize','LeaveCriticalSection'))};assert len(inp['APIs'])==5
  return [[site,['typed_API',api[(site,target)]]if(site,target)in api else ['source',target],ret]for site,target,ret in result['calls']]
 assert a['PCs']==b['PCs']and calls(a,ain)==calls(b,binp)and a['returns']==b['returns'];assert a['constructor_flag_consumers']==b['constructor_flag_consumers'];assert a['source_API_inputs']==b['source_API_inputs']==5
 aa=sorted(a['source_complete_owners'],key=lambda o:o['generation']);bb=sorted(b['source_complete_owners'],key=lambda o:o['generation']);assert len({o['generation']for o in aa})==len(aa)and len({o['generation']for o in bb})==len(bb);assert len({y['generation']-x['generation']for x,y in zip(aa,bb)})==1;assert len(aa)==len(bb);assert all(x.get('live',True)and y.get('live',True)for x,y in zip(aa,bb))
 def value(v,owners):
  found=[(i,v-o['guest'])for i,o in enumerate(owners)if o['guest']<=v<o['guest']+o['extent']];assert len(found)<=1;return ['owner',*found[0]]if found else ['literal',v]
 def words(raw,owners):assert len(raw)%4==0;return [value(v,owners)for v in struct.unpack('<'+'I'*(len(raw)//4),raw)]
 for current,first in((aa,firsta),(bb,firstb)):
  initial_roles=sorted(first['owners'],key=lambda o:o['generation']);assert len(initial_roles)==8
  for i in range(1,8):
   own=initial_roles[i];assert struct.unpack_from('<2I',bytes.fromhex(own['initial_hex']))==(own['guest'],own['guest']);assert current[i]['guest']==own['guest']and current[i]['generation']==own['generation'];assert bytes.fromhex(current[i]['initial_hex'])[8:12]==bytes.fromhex(own['initial_hex'])[8:12]
 original_births={}
 for earlier_root in (0x4103f0,0x410440,0x459b40):
  earlier=earlier_original_derivations[earlier_root]
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
 return dict(sequence=seq,root=root,branch=level,exact_literal_PC_call_return_path=True,exact_flag_consumers=True,whole_typed_global5F2000=True,whole_source_logical_owner_fields=owner_rows,exact_source_owned_writes=len(a['constructor_owned_writes']),exact_balanced_FS_events=len(a['constructor_FS']),source_API_occurrences=5,original_whole_State_claim=False,complete_constructor_acceptance_gate=False)

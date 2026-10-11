"""Separate finite actual indirect-call/source causality receipt for120."""
from pathlib import Path
import collections,hashlib,json,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-next-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh actual indirect source receipt');out.mkdir();pins={};counts=collections.Counter();pairs=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact frozen indirect source dependency');pins[str(p)]=v;return p
 def report(p):
  r=json.loads(pin(p).read_bytes());need(r['passed'],'Only passed current source gate');return r
 try:
  original=report(BASE/'original-game-source-r1/report.json');native=report(BASE/'connected-native-source-r1/report.json');need(not original['AFTER_machine_seed']and not native['candidate_AFTER_machine_seed']and not native['per_phase_BEFORE_machine_seed'],'Only genuine source BEFORE derivations')
  inputs=json.loads(pin(BASE/'recovery-r1/indirect-call-inputs.json','a329e3988a4d77137e1270d9606c2c65f8b6aee95d1f04fb5928eb9a28a90d9a').read_bytes());bindings={(r['root'],r['CALL_pc']):r for r in inputs};need(len(bindings)==6,'Exactly six rooted physical CALL interfaces')
  allrows=[]
  for branch,r in(('original',original),('native',native)):
   p=BASE/('original-game-source-r1'if branch=='original'else 'connected-native-source-r1')/'indirect-source-derivations.json';rows=json.loads(pin(p,r['files'][str(p.resolve())]).read_bytes());need(len(rows)==(36 if branch=='original'else 72),'Complete current finite source call scope')
   for row in rows:
    binding=bindings[(row['root'],row['CALL_pc'])];need((row['slot'],row['target'],row['return_pc'],row['argument'],row['RET_cleanup'])==tuple(binding[k]for k in('slot','target','return_pc','argument','RET_cleanup')),'Exact physical rooted source interface')
    before,ret,after=(row[k]for k in('ENTRY_BEFORE','RET_BEFORE','RET_AFTER'));need(before['CPU'][1]==ret['CPU'][1]==binding['entry_ECX']and before['ESP']==ret['ESP']and after['ESP']==before['ESP']+4+binding['RET_cleanup'],'Genuine entry/preRET source frame and physical RET cleanup')
    need(before['frame_hex']==ret['frame_hex']and int.from_bytes(bytes.fromhex(before['frame_hex'])[:4],'little')==binding['return_pc'],'Complete unchanged real16B source frame through helper')
    need(before['FX_hex']==ret['FX_hex']==after['FX_hex']and before['ENV_hex']==ret['ENV_hex']==after['ENV_hex'],'Whole normal helper FX/ENV unchanged by literal integer source')
    need(before['FS0']==ret['FS0']==after['FS0'],'Literal pure helper preserves own normal FS context')
    accesses=row['source_accesses'];need(accesses[0]==[binding['CALL_pc'],binding['slot'],binding['target'],4,0],'Physical actual cell source read')
    need(accesses[-1]==[row['RET_pc'],before['ESP'],binding['return_pc'],4,0],'Physical real RET-word source read')
    if binding.get('source_vtable'):
     dom=row['dominating_vptr_store'];need(dom['access']==[binding['dominating_vtable_store_PC'],binding['source_object'],binding['source_vtable'],4,1],'Exact source-established vptr dominates finite indirect calls');counts[branch+'_dominating_vptr_publications']+=1
    if row['target']==0x59ff00:
     g=next(x for x in accesses if x[0]==0x59ff00 and x[1]==0x5f49b8 and x[3:]==[4,0]);rd=next(x for x in accesses if x[0]==0x59ff05 and x[1]==binding['entry_ECX']+12 and x[3:]==[4,0]);wr=next(x for x in accesses if x[0]==0x59ff0a and x[1]==binding['entry_ECX']+12 and x[3:]==[4,1]);result=g[2]|rd[2]
     need(wr[2]==result and ret['CPU'][0]==g[2]and ret['CPU'][2]==result,'Exact actual/source arbitrary-DWORD global OR object byteflow and CPU effects')
     expected_flags=0x202|((result&255).bit_count()%2==0)<<2|(result==0)<<6|(result>>31)<<7|(before['CPU'][8]&(1<<10));need(ret['CPU'][8]==expected_flags,'Complete literal OR flags with declared actual undefined AF zero');counts[branch+'_whole_OR_CPU_flags_prefixes']+=1
    elif row['target']==0x40e820:
     need(row['argument']==0 and ret['CPU'][0]==0 and ret['CPU'][8]==before['CPU'][8]and [0x40e824,binding['entry_ECX']+4,0,4,1]in accesses,'Exact source zero-field MOV and unchanged complete flags')
    else:
     need(row['target']==0x59ff80 and row['argument']==0 and row['actual_prefix_PCs']==[0x59ff6e,0x59ff80,0x59ff84,0x59ff86,0x59ffa1]and not any(0x59ff88<=x[0]<=0x59ff9e for x in accesses),'Only true null argument normal prefix, zero pointee accesses');counts[branch+'_zero_argument_no_pointee_prefixes']+=1
    if branch=='original':
     observations=row['actual_original_snapshots'];need(len(observations)==2 and observations[0]['point']==0 and observations[1]['point']==1,'True original target entry and preRET observations')
     need(observations[0]['CPU']==before['CPU']and observations[1]['CPU']==ret['CPU']and observations[0]['meta'][15]==observations[1]['meta'][15],'Actual complete original CPU/flags and zero API effects already source-joined');counts['actual_original_full_CPU_FX_ENV_boundaries']+=2;counts['actual_original_CALL_preRET_joins']+=1
    else:
     w=row['actual_native_witness'];need(w[21]==1 and len(row['actual_native_checkpoints'])==2 and row['actual_native_source_access_prefix']==accesses,'True native source CALL/RET plus full State/CPU/FX and entire journal prefix joins')
     need(w[24]==w[25]and w[26]==w[27]and w[28]==w[29],'Actual zero FS/API/owner effects')
     if row['CALL_pc']==0x59fdc5:need(w[13]==0,'Fixed absolute cell declares zero actual instance-vptr read index')
     if row['CALL_pc']==0x59ff6e:need(w[13]>w[12],'Actual instance-vptr source read follows real dominating publication')
     counts['actual_native_full_State_CPU_FX_boundaries']+=2;counts['actual_native_CALL_RET_joins']+=1;counts['whole_actual_native_source_prefixes']+=1
    row['branch']=branch;allrows.append(row)
  for seq in range(6):
   old={(r['root'],r['CALL_pc']):r for r in allrows if r['branch']=='original'and r['sequence']==seq};need(set(old)==set(bindings),'Each original sequence reaches all six exact calls')
   for level in('O0','O2'):
    current={(r['root'],r['CALL_pc']):r for r in allrows if r['branch']=='native'and r['sequence']==seq and r['level']==level};need(set(current)==set(old),'Exact six corresponding native/original call sets')
    for key in old:pairs.append(dict(level=level,sequence=seq,root=key[0],CALL_pc=key[1],target=old[key]['target'],original_entry_CPU=old[key]['ENTRY_BEFORE']['CPU'],native_entry_CPU=current[key]['ENTRY_BEFORE']['CPU'],original_preRET_CPU=old[key]['RET_BEFORE']['CPU'],native_preRET_CPU=current[key]['RET_BEFORE']['CPU'],whole_crossbranch_volatile_CPU_equality_claimed=False));counts['paired_source_CALL_interfaces']+=1
  need(counts['actual_original_CALL_preRET_joins']==36 and counts['actual_native_CALL_RET_joins']==72 and counts['paired_source_CALL_interfaces']==72,'All required actual finite joins')
  pin(__file__);pin(ROOT/'tools/m4-next-source/indirect_trace.py');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'call-relations.json').write_text(json.dumps(pairs,indent=2)+'\n');pin(out/'call-relations.json');r=dict(passed=passed,scope='Six finite rooted fixed dispatches:36 actual original target-entry/preRET pairs and72 actual native CALL/RET/fullStateCPUFX pairs, literal entire source prefixes, raw physical cells, committed instance vptr and separate absolute-cell metadata, arbitrary-DWORD OR effects/complete flags, zero pointer constructor with no pointee reads.',counts=dict(counts),AFTER_machine_seed=False,per_phase_machine_seed=False,original_postRET_CPU_source_derived_only=True,whole_crossbranch_volatile_CPU_equality_claimed=False,new_provider_or_owner_operations=0,nonzero_pointer_path_admitted=False,handler_execution=False,initializer_credit=False,files=pins);(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])

"""Prepared finite constructor root-entry FS prediction and stale-checkpoint domain review."""
import struct
FIRST_FS={0x4103f0:0x4c0317,0x410440:0x4c0577,0x459b40:0x459b87}
def need(v,s):
 if not v:raise ValueError(s)
def prior_domains(prior_pages,own_phase_pages):
 need(all(type(a)is int and type(n)is int and n>0 for a,n in prior_pages.items()),'Exact prior region schema')
 missing=set(prior_pages)-set(own_phase_pages);need(not missing,'No surviving earlier-checkpoint region may substitute for genuine root BEFORE')
 return dict(prior_regions=len(prior_pages),surviving_prior_regions=0,earlier_checkpoint_nonphase_input_dependency_present=False)
def FS_cut(root,state,before_raw,after_raw,carried,contracts):
 need(root in FIRST_FS and len(state)==3504 and struct.unpack_from('<I',state,2168)[0]==0x7ffde000,'Actual own root State FS base equals current native Runtime policy')
 need(carried['root']==root and carried['source_seed']is False and carried['AFTER_seed']is False and carried['whole_native_component_journals_compared']is True,'Current own carried literal component source authority')
 need(len(before_raw)%24==len(after_raw)%24==0 and after_raw.startswith(before_raw),'Actual cumulative whole component ledger prefix')
 delta=[list(v)for v in struct.iter_unpack('<IIQII',after_raw[len(before_raw):])];need(delta==carried['component_source_accesses'],'Every actual own ordered component operand joins current carried literal source')
 fs=0x7ffde000;overlap=lambda v:v[1]<fs+4 and v[1]+v[3]>fs
 indices=[i for i,v in enumerate(delta)if overlap(v)];need(indices,'Own component first FS operand exists');i=indices[0];expected=[FIRST_FS[root],fs,0xffffffff,4,0];need(delta[i]==expected and i==3,'Exact first literal normal FS DWORD read corroborates independently predicted Runtime/scope sentinel')
 need(not any(v[4]and overlap(v)for v in delta[:i]),'No preceding source write overlaps any of four FS bytes')
 need(FIRST_FS[root]in {v['read']for v in contracts['frames']},'Exact physical declared constructor FS source PC')
 whole=carried['whole_literal_source_accesses'];need(whole[:i+1]==delta[:i+1],'Before first borrowed call, complete literal component/provider sequence equals actual component prefix')
 events=carried['game_FS_observations'];need(events and events[0]['root']==root and events[0]['PC']==FIRST_FS[root]and events[0]['kind']==0 and events[0]['before_head']==0xffffffff,'First current own source FS observation corroborates ROOT ENTRY restored-sentinel guard')
 return dict(address=fs,bytes=4,predicted_value=0xffffffff,hex=struct.pack('<I',0xffffffff).hex(),source_PC=FIRST_FS[root],source_access_index=i,input_cut_authority='Runtime initialization and exact same-instance constructor_scope entry guard before component BEFORE checkpoint; current first read is corroboration only',whole_TIB_claim=False,no_prior_FS_write=True,observed_AFTER_value_used_as_seed=False)

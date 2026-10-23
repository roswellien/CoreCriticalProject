"""Pure physical broker CPU derivations; no State constructor or executor."""
FRAME=0x20001800
BROKER=0x410a80
ROOT=0x4b5910
FOLLOWING=0x4b5af0
def original_input(previous_after,target):
 assert len(previous_after)==10 and previous_after[4]==FRAME+4 and previous_after[9]==BROKER
 result=list(previous_after);result[4]=FRAME;result[9]=target
 return result,dict(address=FRAME,bytes=4,value=BROKER,producer='original reference mixed_input setter plus mixed_enter authored JMP/RET bracket',hypot_body_executed=False)
def native_call(previous_after,target):
 assert len(previous_after)==10 and previous_after[4]==FRAME+4 and previous_after[9]==BROKER
 result=list(previous_after);result[4]-=4;result[9]=target
 return result,dict(address=FRAME,bytes=4,value=BROKER,producer='Runtime::call pending Cdecl0 frame store and CPU ESP/EIP transition',hypot_body_executed=False)
def retarget_measured_following_before(previous_after,observed_before,native):
 assert len(observed_before)==10 and observed_before[4]==FRAME and observed_before[9]==FOLLOWING
 derive=native_call if native else original_input
 predicted,word=derive(previous_after,FOLLOWING);assert predicted==list(observed_before),'Entire existing pending next-root CPU joins physical broker transition'
 candidate,word=derive(previous_after,ROOT)
 assert all(candidate[i]==observed_before[i]for i in range(10)if i!=9)
 return dict(source_derived_candidate_CPU=candidate,committed_return_word=word,observed_root=FOLLOWING,candidate_root=ROOT,candidate_CPU_observed=False,whole_candidate_State_constructed=False,source_definedness_metadata_proven=False)

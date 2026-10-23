"""Conditional finite paired ENV relation kernel; upstream lastwriter admission mandatory."""
EXPECTED_EPOCH_ENV=bytes.fromhex('7f00ffff2040ffffffffffff18e64c0023001d0194b460002b00ffff')
ROOTS={137:0x5a3c30,138:0x5a3ff0,139:0x5a66f0,140:0x5a7dc0}
def need(v,s):
 if not v:raise ValueError(s)
def active(sequence,phase,side):
 need(type(sequence)is int and type(phase)is int and 0<=sequence<6 and 0<=phase<141 and side in('before','after'),'Exact current selected endpoint identity')
 return sequence==0 and ((side=='after'and 137<=phase<=140)or(side=='before'and 138<=phase<=140))
def compare(sequence,phase,side,root,epoch_before_State,endpoint_State,original_ENV,native_ENV,project):
 need(type(original_ENV)is bytes and type(native_ENV)is bytes and len(original_ENV)==len(native_ENV)==28,'Whole paired ENV28 targets')
 need(type(endpoint_State)is bytes and len(endpoint_State)==3504 and project(endpoint_State)==native_ENV,'Entire native endpoint ENV equals physically admitted complete State projector')
 if not active(sequence,phase,side):need(original_ENV==native_ENV,'Whole ENV outside finite current original clear epoch');return dict(whole_ENV28_compared=True,typed_original_metadata_clear=False,bytes_excluded=0)
 need(root==ROOTS[phase]and type(epoch_before_State)is bytes and len(epoch_before_State)==3504,'Exact current sourcebound genuine phase137 BEFORE metadata input')
 initial=project(epoch_before_State);need(initial==EXPECTED_EPOCH_ENV,'Own sourcebound native epoch input independently joins original finite event BEFORE, not any AFTER value')
 need(native_ENV[12:26]==initial[12:26],'Native metadata retains entire known last-source-writer fourteen bytes')
 predicted=native_ENV[:12]+bytes(14)+native_ENV[26:]
 need(original_ENV==predicted,'Entire original ENV equals independently specified original API metadata clear plus exact head/reserved bytes')
 return dict(whole_ENV28_compared=True,typed_original_metadata_clear=True,metadata_bytes_predicted=14,bytes_excluded=0,whole_FX_rule_owned_by_unchanged_parent=True,API_body_execution_claim=False)

"""Bind the complete lifecycle source proof and distinguish producer source-free."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_witnesses_v2.py';s=p.read_text()
s=s.replace('native-source-r4/report.json','native-source-r9/report.json').replace('199ecc9f07316a7f39f4ac936fe349687d7ceaa8d5fbc29a7c442a4d27cf3451','0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306')
a="and before[7:8]==(1,)and before[10:12]==(0,0)and after[10:12]==(0,1)";assert s.count(a)==1
s=s.replace(a,"and before[7]==before[8]and before[10:12]==(0,0)and after[10:12]==((1,0)if before[1]==0x31000000 else(0,1))")
a="summary[9:16]==(4,0,4,5,5,0,0)";assert s.count(a)==1;s=s.replace(a,"summary[9:16]==(4,1,3,5,5,0,0)")
a="   equal(a.data('actual-causal-State.bin'),a.data('sample.bin')[768+3504:768+7008],'Outside-return complete guest State unchanged by cleanup');counts['outside_return_whole_State']+=1";assert s.count(a)==1
s=s.replace(a,"   need(source['counts']['complete_actual_lifecycles']==2 and source['counts']['literal_producer_source_frees']==2,'Authoritative source receipt derives complete postcleanup State/CPU and source producer release');counts['outside_return_whole_State_source_proofs_consumed']+=1")
target=R/'tools/m4-formatting-source/compare_native_witnesses_v3.py';assert not target.exists();target.write_text(s)

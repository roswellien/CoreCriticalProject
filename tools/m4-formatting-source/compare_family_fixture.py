"""Execute complete persistent source/provider/owner/cleanup comparison for four roots."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('compare_native_fixture_v9.py');s=p.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
one('ROOTS=(0x4df610,0x4e0710,0x4e0810)','ROOTS=(0x4df610,0x4e0710,0x4e0810,0x4e1ca0)')
one("fixture-execution-r4/report.json','55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0'","family-fixture-execution-r1/report.json','5ecd8260c6625a589c8e1c517b41c1c7f8deddfbbeb1b61825f6e337c1767297'")
one("persistent-model-r3/report.json','8a6f4968d524105ea04aeaa4c08a78ec2a259cf6b279ff719ddc0cabf05ad9cf'","persistent-family-model-r1/report.json','53c2a9f6dc3ede4ed5b089ff7c92490bbcdd4113679fc35ba830a4e359f50887'")
one('R.EXPECTED_LOCKIT_CALLS=0','R.EXPECTED_LOCKIT_CALLS=2')
one("resource=reader.words(stem+'lockit-resource.bin',8,'Q');need(reader.data(stem+'lockit-native-images.bin')==b'','No rooted Lockit calls in isolated formatter3')","resource=reader.words(stem+'lockit-resource.bin',8,'Q');raw_images=reader.data(stem+'lockit-native-images.bin');need(len(raw_images)==80,'Two whole actual native40 Lockit API outputs');lockit_images=[raw_images[k:k+40]for k in range(0,80,40)]")
one('responses.associate_lockit(machine,resource,[],rw[0x640:0x658])','responses.associate_lockit(machine,resource,lockit_images,rw[0x640:0x658])')
one("len(records)==3*159716,'Three exact Native records'","len(records)==4*159716,'Four exact Native records'")
one("need(len(owner_new)==1,'One actual finite new HeapAlloc per formatter');owner=owner_new[0]","need(len(owner_new)==(4 if entry==0x4e1ca0 else 1),'One formatter allocation plus three literal mixed MFC occurrences');owner=owner_new[0]")
one("owner['requested']==(8,10,12)[phase]","owner['requested']==(8,10,12,11)[phase]")
one("expected_callbacks.append((0x4df680,0x4e07b0,0x4e0850)[phase])","expected_callbacks.append((0x4df680,0x4e07b0,0x4e0850,0x4e1ce0)[phase])")
one("results.append(result);counts['strict_native_phases']+=1",'''if entry==0x4e1ca0:
     mixed=[]
     for role,(actual,requested,site)in enumerate(zip(owner_new[1:],(12,24,24),(0x49cc8d,0x4e5325,0x4e535b))):
      need(actual['requested']==requested and actual['extent']==(16 if requested==12 else 32),'Exact mixed source request and actual capacity')
      matching=[r for r in actual_owners if r[1]==actual['guest']and r[5]==actual['generation']];need(len(matching)==1 and matching[0][6]==4 and matching[0][8]==actual['native'],'Actual mixed MFC kind/native/generation')
      raw=machine.bytes(actual['guest'],actual['extent']);equal(raw,reader.data(f'actual-after-root-{phase}/native-full-{actual["generation"]}.bin'),'Whole actual mixed native backing');equal(raw[requested:],actual['initial'][requested:],'Every mixed requested-to-capacity tail byte preserved')
      ops=[r for r in machine.accesses[access_start:]if actual['guest']<=r[1]and r[1]+r[3]<=actual['guest']+actual['extent']]
      mixed.append(actual|dict(owner_role=role,allocation_CALL_pc=site,initial=actual['initial'].hex(),source_final_hex=raw.hex(),source_owned_accesses=ops));counts['whole_mixed_native_owner_backings']+=1
     result['mixed_owners']=mixed;result['Lockit_API_relations']=list(responses.lockit_relations)
    results.append(result);counts['strict_native_phases']+=1''')
one("len(fmt_calls)==9 and all(c['returned']for c in fmt_calls),'Nine exact source cdecl CALL/RET lifetimes'","len(fmt_calls)==12 and all(c['returned']for c in fmt_calls),'Twelve exact source cdecl CALL/RET lifetimes'")
one("len(machine.output_dispatches)==12 and [d['index']for d in machine.output_dispatches]==[1,7,1,7]*3,'Twelve literal normal source table dispatches');counts['literal_table_dispatches']+=12","len(machine.output_dispatches)==16 and [d['index']for d in machine.output_dispatches]==[1,7,1,7]*4,'Sixteen literal normal source table dispatches');counts['literal_table_dispatches']+=16")
one("producer=responses.allocations[0];oldsp=machine.reg('esp');oldpc=machine.word(2472)",'''for allocation in responses.allocations:
    if allocation['requested']not in(12,24)or allocation['guest']==responses.allocations[0]['guest']or not allocation['live']:continue
    oldsp=machine.reg('esp');oldpc=machine.word(2472);machine.write(oldsp-4,allocation['guest'],domain='research',pc=oldpc);machine.reg('esp',oldsp-4);machine.invoke_external(0x5f401770,0xffffff50,responses);machine.reg('esp',oldsp);machine.cpu=B.cpu(machine.state)
    need(not allocation['live'],'Literal MFC825/CRTfree retires whole actual mixed backing');counts['literal_mixed_MFC_source_frees']+=1
   producer=responses.allocations[0];oldsp=machine.reg('esp');oldpc=machine.word(2472)''')
one("for owner in reversed(responses.allocations[1:]):\n    fact=","for owner in reversed(responses.allocations[1:]):\n    if not owner['live']:continue\n    fact=")
one("pin(__file__)\n  for p in list(READS)","pin(__file__);pin(ROOT/'tools/m4-formatting-source/compare_native_fixture_v9.py')\n  for p in list(READS)")
s=s.replace('formatter3','formatter4')
exec(compile(s,str(p),'exec'),globals())

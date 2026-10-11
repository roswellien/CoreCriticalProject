"""Focused mixed source-role/private-frame faults and exact cleanup/retry checks."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('check_formatting_controls_v2.py');s=p.read_text()
for a,b in [("p['control_scenarios']==14 and p['control_attempts']==28","p['control_scenarios']==10 and p['control_attempts']==20"),('bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3'),('Frozen native15','Frozen native19'),('(1,14,28,9968,0x4df610,3504,40,512,70)','(1,10,20,9968,0x4e1ca0,3504,40,512,70)'),('range(14)','range(10)'),('o[2] in (8,10,12)','o[2] in (8,10,12,11)'),('tags[4]==3 and not any(tags[k] for k in (10,11,12,13))','tags[4]==4 and tags[10:14]==(2,3,0,0)'),("[1:3]==(0,3)","[1:3]==(0,4)"),('==9 and len(rows(a,live+\'formatting-owned.bin\',\'<12Q\'))==33','==12 and len(rows(a,live+\'formatting-owned.bin\',\'<12Q\'))==45'),("formatting-publications.bin','<12Q'))==3", "formatting-publications.bin','<12Q'))==4"),("formatting-dispatches.bin','<8Q'))==12","formatting-dispatches.bin','<8Q'))==16"),("counts['registered_positive_roots']+=3", "counts['registered_positive_roots']+=4"),('not tags[3] and not tags[4] and tags[12]','not tags[3] and tags[4]==3 and tags[12]'),("counts['causal_denials']==26 and counts['same_session_refusals']==28 and counts['registered_positive_roots']==6","counts['causal_denials']==18 and counts['same_session_refusals']==20 and counts['registered_positive_roots']==8")]:
 assert a in s,a;s=s.replace(a,b)
a="hardware(sample[8880:9424],sample[9424:9968],True); hardware(a.data(root+'actual-cleanup-hardware-before.bin'),a.data(root+'actual-cleanup-hardware-after.bin'))"
b=a+"; hardware(a.data(root+'actual-invocation-hardware-before.bin'),a.data(root+'actual-invocation-hardware-after.bin'));counts['immediate_Context_architectural_hardware_pairs']+=1"
assert s.count(a)==1;s=s.replace(a,b)
a="'formatting-dispatches.bin','current-page-addresses.bin')"
b="'formatting-dispatches.bin','fs-chain-events.bin','fs-active-records.bin','fs-record-bytes.bin','fs-owned-accesses.bin','fs-owned-publications.bin','fs-chain-probe.bin','mfc-allocation-witnesses.bin','lockit-calls.bin','lockit-imports.bin','lockit-source-CS.bin','lockit-native-images.bin','current-page-addresses.bin')"
assert s.count(a)==1;s=s.replace(a,b)
a="                        if case==0:\n"
b="""                        # Every acquired MFC byte, including untouched capacity, follows only its actual initial and committed literal stores.
                        for o in allocs:
                            if o[6]!=4 or not o[9]:continue
                            need(o[2]in(12,24)and o[3]==(16 if o[2]==12 else 32)and o[4]==4096 and o[8]and o[5],'Actual mixed MFC request/capacity/current native generation')
                            stem=live+f'locale-allocation-{o[5]}';initial=a.data(stem+'-initial.bin');need(len(initial)==o[3],'Entire actual MFC acquired initial capacity');want=bytearray(initial+bytes(4096-o[3]))
                            for pc,address,value,width,writing in accesses:
                                if writing and o[1]<=address<o[1]+4096:
                                    need(width==4 and address+width<=o[1]+o[2],'No faulting source candidate commits outside requested MFC domain');want[address-o[1]:address-o[1]+width]=value.to_bytes(width,'little');counts['mixed_literal_owner_stores']+=1
                            need(bytes(want)==a.data(stem+'-expected.bin')==a.data(stem+'-owned-page.bin')and bytes(want[:o[3]])==a.data(live+f'native-full-{o[5]}.bin')and want[o[2]:o[3]]==initial[o[2]:],'Full actual MFC page/native capacity/tail derived from own initial plus committed stores');counts['whole_mixed_owner_backing_byteflows']+=1
                        cleaned=rows(a,clean+'locale-allocations.bin','<16Q');need(len(cleaned)==len(allocs),'Cleanup retains every actual acquisition identity')
                        for old,new in zip(allocs,cleaned):need(old[:8]==new[:8]and new[8:10]==(0,0)and sum(new[10:12])==1,'Exact current generation is freed once and its guest alias revoked');counts['actual_acquisition_cleanup_joins']+=1
                        if case==0:
                            mfc=rows(a,live+'mfc-allocation-witnesses.bin','<32Q');owned=rows(a,live+'fs-owned-accesses.bin','<16Q');pubs=rows(a,live+'fs-owned-publications.bin','<16Q')
                            need(len(mfc)==3 and len(owned)==10 and len(pubs)==3,'Exact complete positive mixed MFC/private extents')
                            for i,w in enumerate(owned):
                                current=next(o for o in allocs if o[1]==w[10]and o[5]==w[11]);r=next(r for r in mfc if r[16]==w[10]and r[18]==w[11]);source=accesses[w[15]-1]
                                want=(1,i,0x4e1ca0,source[0],source[1],source[3],source[2],source[4],r[2],r[4],current[1],current[5],current[8],source[1]-current[1],r[1],w[15]);need(w==want,'Every full16Q positive mixed private operand joins actual current MFC source access');counts['positive_mixed_private16Q_access_joins']+=1
                            for i,w in enumerate(pubs):
                                r=next(r for r in mfc if r[16]==w[5]and r[18]==w[6]);source=accesses[w[12]-1];need(source==(w[3],w[4],w[5],4,1)and w==(1,i,0x4e1ca0,w[3],w[4],w[5],r[18],r[17],r[4],0,0,0,w[12],({0x49cc8d:6338380,0x4e5325:6338152,0x4e535b:6338152}[r[4]]),0,0),'Every full16Q one-time mixed static publication binds its own occurrence');counts['positive_mixed_private16Q_publication_joins']+=1
                            need(len(a.data(root+'actual-root-records.bin'))==4*159716,'Four complete genuine Runtime-selected Native records')
"""
assert s.count(a)==1;s=s.replace(a,b)
start=s.index('                        if case<=4:');end=s.index('                        causes.append(',start)
s=s[:start]+"""                        expected_pc=0x49cc95 if case in(1,2,6)else 0x4e532a if case==7 else 0x4e5360
                        need(identity[:2]==(87 if case==6 else 86,expected_pc),'Exact real mixed source owner hook and PC')
                        if case<=5:
                            need(v[0]==1 and v[5]and v[6]and v[7]==case and v[8]==expected_pc and v[10]==4,'Real decoded DWORD source write counterfactual')
                            owners=rows(a,trig+'locale-allocations.bin','<16Q');current=next(o for o in owners if o[1]==v[5]and o[5]==v[6]);need(current[6]==4 and current[8]and current[9],'Original source operand carries real current MFC owner generation')
                            target=next((o for o in owners if o[1]<=v[1]<o[1]+o[4]),None);need(target is not None,'Actual counterfactual target mapped owner domain')
                            need(a.data(trig+f'locale-allocation-{target[5]}-owned-page.bin')==a.data(live+f'locale-allocation-{target[5]}-owned-page.bin'),'Entire actual target unchanged before denied source commit')
                            if case==1:need(target[6]==1 and target[1]==v[13]!=current[1]and v[1]==v[2]==v[13],'Foreign real generic malloc owner is refused by exact MFC kind/role')
                            if case==2:need(target==current and v[1]==v[2]==current[1]+12 and current[2:4]==(12,16),'Requested-tail DWORD remains within real physical capacity16')
                            if case==3:need(current[1]==v[12]and v[1]==v[11]+4 and target[1]==v[11]and current[2]==target[2]==24,'Distinct real sentinel/header occurrence at same24 requested size')
                            if case==4:need(v[1]==current[1]+4 and v[2]==v[12]==current[1]and v[4]==v[11]!=v[12],'Correct cell with wrong exact parent owner pointer')
                            if case==5:need(v[9]==0x4e532a and v[1]==current[1]+4 and not v[2],'Real earlier header-store PC attempted on current sentinel occurrence')
                            expected='Mixed source scalar/pointer value derives from its exact role'if case==4 else'Mixed exact live MFC role/generation/PC/offset/width/order'
                            need(reason==expected and fault[1]==v[9]and fault[2]==v[1],'Exact actual first source admission reason/address/PC');counts['public_mixed_source_operand_denials']+=1
                        elif case<=7:
                            old=a.data(trig+'private-before.bin');new=a.data(trig+'private-after.bin');name=a.data(trig+'private-name.bin').decode();need(v[0]==2 and v[1]<len(old)==len(new)==v[2]and sum((x^y).bit_count()for x,y in zip(old,new))==1,'Exactly one actual private ledger bit intervention');need(name==('fs-owned-accesses.bin'if case==6 else'fs-owned-publications.bin')and v[1]==(11 if case==6 else 6)*8 and a.data(live+name)==new,'Actual mixed generation field corruption reaches firstfault intact');need(reason=='FS observer changed private source-frame/chain witnesses','Precise genuine private FS conservation predicate');counts['mixed_private_witness_denials']+=1
                        else:
                            need(v[0]==4 and v[3]==(v[2]^(4 if case==8 else 1))and v[4]==4,'One genuine current guest DWORD changed')
                            if case==8:need(v[1]==0x5bb4f4 and reason=='Only committed source/API/research effects may change owned locale pages'and fault[2]==0x5bb000,'Actual named dtorIAT cell conservation firstfault')
                            if case==9:need(reason=='Installed source FS predecessor/handler and active private frame identity'and fault[2]+4==v[1],'Actual installed complete FS handler conservation firstfault')
                            counts['mixed_IAT_or_FS_denials']+=1
"""+s[end:]
s=s.replace('public_source_service=case<=4 or case==9','public_source_service=case<=5')
s=s.replace("pin(__file__); pin(R/'tools/m4-tree-review/check_controls_v3.py')","pin(__file__); pin(R/'tools/m4-tree-review/check_formatting_controls_v2.py'); pin(R/'tools/m4-tree-review/check_controls_v3.py')")
s=s.replace('Focused actual registered formatter3 controls:','Focused actual registered native19 mixed four-root controls:')
s=s.replace('def main(execution, digest, name):',"def main(execution, digest, name, levels=('O0','O2')):")
s=s.replace("for level in ('O0','O2'):","for level in levels:")
s=s.replace("counts['causal_denials']==18 and counts['same_session_refusals']==20 and counts['registered_positive_roots']==8", "counts['causal_denials']==9*len(levels) and counts['same_session_refusals']==10*len(levels) and counts['registered_positive_roots']==4*len(levels)")
s=s.replace("counts=dict(counts),reader_closed=True", "counts=dict(counts),levels=list(levels),reader_closed=True")
s=s.replace("main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])", "main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3],tuple(sys.argv[4:])or('O0','O2'))")
exec(compile(s,str(p),'exec'),globals())

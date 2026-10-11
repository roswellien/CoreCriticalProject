"""Prepare current own-provider-page source comparer; no output is consumed."""
from pathlib import Path
import ast,hashlib
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-fps-native/derive_source.py';target=R/'tools/m4-fps-native/derive_source_current.py'
assert not target.exists();t=parent.read_text()
for a,b,n in [
 ("target=R/'tools/m4-fps-native/compare_prefix.py'","target=R/'tools/m4-fps-native/compare_prefix_v2.py'",1),
 ('fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7','636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a',1),
 ('e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc','bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0',1),
 ("'reports/m4-fps-native/fixture-build-r1'","'reports/m4-fps-native/fixture-build-r2'",1),
 ("'reports/m4-fps-native/fixture-preparation-r1'","'reports/m4-fps-native/fixture-preparation-r2'",1),
 ("R/'reports/m4-fps-native/controller-preparation-r1/report.json'","R/'reports/m4-fps-native/controller-preparation-r3/report.json'",1),
]:
 assert t.count(a)==n,(a,t.count(a));t=t.replace(a,b)
marker=" ast.parse(text);target.write_text(text);pin(target)"
assert t.count(marker)==1
insert=''' replace(" memory[0x20001000]=bytearray(raw(folder/'stack.bin'))", """ for f in sorted(folder.glob('provider-source-page-*.bin')):
  address=int(f.stem.removeprefix('provider-source-page-'));b=raw(f);need(len(b)==4096 and not any(a<address+4096 and address<a+len(v)for a,v in memory.items()),'Whole nonoverlapping current provider source input page');memory[address]=bytearray(b)
 need({address for address in memory if address>=0x78000000}=={0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000},'Five exact own provider BEFORE source pages')
 memory[0x20001000]=bytearray(raw(folder/'stack.bin'))""")
 replace("    derivations.append(dict(level=level,phase=phase,root=root_pc", """    for f in sorted((phase_dir/'before').glob('provider-source-page-*.bin')):
     address=int(f.stem.removeprefix('provider-source-page-'));expected=raw(f)
     if address==0x78037000:
      observed=raw(prefix/f'registry-checkpoint-{n}-page-{address}.bin');eq(m.bytes(address,4096),observed,'Whole carried CRT RW page at source-derived actual registry provider entry')
     else:
      observed=raw(phase_dir/'after'/f.name);eq(m.bytes(address,4096),observed,'Whole provider source/readonly page carried through literal current prefix and registry service')
     counts['whole_current_provider_source_page_joins']+=1
    derivations.append(dict(level=level,phase=phase,root=root_pc""")
 replace("counts['literal_formatter_lifetimes']==2 and counts['literal_character_dispatches']==6", "counts['literal_formatter_lifetimes']==2 and counts['literal_character_dispatches']==6 and counts['whole_current_provider_source_page_joins']==70")
 pin(R/'tools/m4-fps-native/derive_source.py');pin(R/'tools/m4-fps-native/derive_source_v2.py');pin(R/'reports/m4-fps-native/fixture-preparation-r2/provider-page-contracts.json')
 ast.parse(text);target.write_text(text);pin(target)'''
t=t.replace(marker,insert);ast.parse(t);target.write_text(t);print(target,hashlib.sha256(target.read_bytes()).hexdigest())

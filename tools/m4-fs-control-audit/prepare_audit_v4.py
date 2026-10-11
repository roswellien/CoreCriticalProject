"""Add complete wrapper bytecode ranges and stronger immutable source checks."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-fs-control-audit/audit_v3.py';s=p.read_text()
a="dis=subprocess.run([str(llvm/'llvm-objdump.exe'),'-dr','--disassemble-symbols='+syms[0],str(obj)]"
b="start=int(next(x.split()[0]for x in nm.splitlines()if x.split()[-1:]==syms),16);dis=subprocess.run([str(llvm/'llvm-objdump.exe'),'-dr','--start-address='+str(start),'--stop-address='+str(start+0x500),str(obj)]"
assert s.count(a)==1;s=s.replace(a,b)
a="  native=json.loads(pin(R/'reports/m4-fs-native/preparation-r3/report.json').read_bytes());need(native['passed'],'Frozen source derivative preparation')"
b=a+"""
  seal=json.loads(pin(R/'reports/m4-fs-controls/source-seal-r1/report.json','b52e8f72c0cf832ea2c591b623caa5163d4eb7a9e68989954c428255ca7298c4').read_bytes());need(seal['passed'],'Final byte-identical compiled fixture/checker seal')
  checked=json.loads(pin(seal['checker'],seal['checker_sha256']).read_bytes());need(checked['passed'],'Final strict producer checker')
  for c in seal['copies']:need(pin(c['source'],c['sha256']).read_bytes()==pin(c['copy'],c['sha256']).read_bytes(),'Exact frozen source copies')
"""
assert s.count(a)==1;s=s.replace(a,b)
a="inst={q['pc']:q for q in contracts['instructions']}"
b=a+"""
  PE=load('fs_byte_bound_PE',pin(R/'tools/analysis/pe.py'));game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  for ins in inst.values():
   offset,size=game.rva_range(ins['pc']-game.image_base,ins['width']);need(game.read(offset,size)==bytes.fromhex(ins['bytes_hex']),'Every original literal FS/MFC game row physically authenticated')
  footprints=json.loads(pin(R/'reports/m4-fs-source/allocation-interface-r1/shared-owner-accesses.json').read_bytes())
"""
assert s.count(a)==1;s=s.replace(a,b)
a="     counts['retry_equal_records']+=len(names);counts['full_machine_retries']+=1"
b="""     retry_clean=stem+'retry-cleaned/';need({n[len(retry_clean):]for n in a.entries if n.startswith(retry_clean)}==names,'Complete retry cleanup observation domain')
     for n in names:need(a.data(clean+n)==a.data(retry_clean+n),'Retry finish performs no additional raw captured work: '+n)
     counts['retry_equal_records']+=2*len(names);counts['full_machine_retries']+=1"""
assert s.count(a)==1;s=s.replace(a,b)
a="     # Full software State projection of guest ENV, distinct from measured host ENV."
insert="""     owner_accesses=rows(a.data(live+'fs-owned-accesses.bin'),16)
     for access in owner_accesses:
      need(access[0]==1 and owner_accesses[access[1]]==access and access[15]<=len(source),'Indexed genuine owned access retains finite literal source prefix')
      al=next(q for q in allocations if q[5]==access[11]);owner=mfc[access[14]]
      need((al[1],al[5],al[7])==(access[10],access[11],access[12])and owner[18]==al[5]and access[4]==al[1]+access[13]and access[4]+access[5]<=al[1]+al[2],'Precise complete owner/generation/requested offset identity')
      need(any((p['root'],p['pc'],p['bytes'],int(p['write']),p['owner_root'],p['owner_CALL_pc'],p['owner_offset'])==(access[2],access[3],access[5],access[7],access[8],access[9],access[13])for p in footprints),'Exact literal admitted shared access geometry, no all-prior-node exemption')
      value=access[6]^1 if case==22 and access==owner_accesses[-1]else access[6]
      need(source[access[15]-1]==(access[3],access[4],value,access[5],access[7]),'Raw source ledger independently supplies genuine value; declared case22 private witness mutation retained')
      counts['precise_shared_owner_accesses']+=1
"""
assert s.count(a)==1;s=s.replace(a,insert+a)
a="      graphs=rows(a.data(live+'fs-shared-graph-witnesses.bin'),16);need([q[7]for q in graphs]==[1,2,3,4,5],'True persistent circular shared list grows exactly five times')"
insert="""
      for graph in graphs:
       before={}
       for owner in mfc:
        al=next(q for q in allocations if q[5]==owner[18]);b=bytearray(a.data(live+f'locale-allocation-{owner[18]}-initial.bin'))
        for pc,address,value,width,writing in source[:graph[15]]:
         if writing and al[1]<=address<al[1]+al[2]:b[address-al[1]:address-al[1]+width]=value.to_bytes(8,'little')[:width]
        before[al[1]]=b
       word=lambda base,offset:struct.unpack_from('<I',before[base],offset)[0]
       container,stop,count=graph[3],graph[5],graph[7];need(word(container,4)==stop and word(container,8)==count,'Actual source-derived registry count and same owned sentinel')
       node=word(stop,4);previous=stop
       for i in range(count):
        owner=next(q for q in mfc if q[16]==node);need(node==graph[8+i]and word(node,0)==previous and word(node,8)==specs[owner[2],owner[4]]['object'],'Actual prior-node cross-root links and exact static object from source prefix')
        previous=node;node=word(node,4)
       need(node==stop and word(stop,0)==previous,'Entire source-derived circular graph closes at the same live owned sentinel');counts['independent_complete_shared_graphs']+=1
"""
assert s.count(a)==1;s=s.replace(a,a+insert)
a="      if case>=21:"
insert="""      if case in(1,2,3,4,5,6,7,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23):
       expected_state=bytearray(a.data(trig+'State.bin'))
       if case==1:
        # State FS-base offset is physically exported by the pinned Remill ABI.
        diff=[i for i,(x,y)in enumerate(zip(expected_state,state))if x!=y];need(len(diff)==1 and expected_state[diff[0]]^state[diff[0]]==4,'Only declared State FS-base mutation reaches stable observer guard')
       else:need(bytes(expected_state)==state,'Direct observer refusal/guard preserves all3504 actual source State bytes at its exact frontier')
       counts['complete_trigger_causal_State_relations']+=1
      elif case==8:
       expected_state=bytearray(a.data(trig+'State.bin'));struct.pack_into('<I',expected_state,2296,q[16]);struct.pack_into('<I',expected_state,2472,0x4e797d)
       need(bytes(expected_state)==state,'Literal MOV EDI then next refused store are the only complete State effects after committed sentinel hook');counts['complete_trigger_causal_State_relations']+=1
"""
assert s.count(a)==1;s=s.replace(a,insert+a)
t=p.with_name('audit_v4.py');assert not t.exists();t.write_text(s)

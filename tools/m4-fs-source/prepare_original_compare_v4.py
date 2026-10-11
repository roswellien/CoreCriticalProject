"""Add exact new local-byte provenance to the passed109 original prefix gate."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];t=(ROOT/'tools/m4-fs-source/compare_original_game_v3.py').read_text()
a='rows=[];ownerrows=[];derivations=[]';assert t.count(a)==1;t=t.replace(a,a+';headerrows=[]')
a='fsbytes=machine.memory[0x7ffde000]';assert t.count(a)==1;t=t.replace(a,a+'''
      if entry==0x4d4830:
       local=machine.accesses;writes=[(i,v)for i,v in enumerate(local)if v[0]==0x4d4922 and v[1]==0x60b51c and v[3:]==(1,1)];need(len(writes)==1,'One literal new FS header source write');wi,write=writes[0];reads=[(i,v)for i,v in enumerate(local[:wi])if v[0]==0x4d4914 and v[3:]==(1,0)];need(len(reads)==1,'Exact literal local byte read');ri,read=reads[0];need(write[2]==read[2],'Literal AL copy to static header');stores=[(i,v)for i,v in enumerate(local[:ri])if v[4]and v[1]<=read[1]<v[1]+v[3]]
       if stores:
        si,store=stores[-1];need((store[2]>>(8*(read[1]-store[1])))&255==read[2],'Exact last source store byte provenance');provenance=dict(kind='dominating_source_store',index=si,pc=store[0],address=store[1],value=store[2],width=store[3])
       else:
        offset=O.PAGES.index(0x20001000)*4096+read[1]-0x20001000;before_stack=b[O.MEM0:O.MEM1];need(before_stack[offset]==read[2],'Exact genuine original branch BEFORE stack byte provenance');provenance=dict(kind='genuine_branch_BEFORE_stack_byte',address=read[1],value=before_stack[offset],no_root_source_store_before_read=True)
       headerrows.append(dict(sequence=seq,phase=phase,root=entry,field=0x60b51c,write_pc=write[0],value=write[2],read_pc=read[0],read_address=read[1],branch_BEFORE_cpu=list(cpu),provenance=provenance))
''')
a="('FS-source-derivations.json',derivations)";assert t.count(a)==1;t=t.replace(a,a+",('new-header-derivations.json',headerrows)")
p=ROOT/'tools/m4-fs-source/compare_original_game_v4.py';assert not p.exists();p.write_text(t)

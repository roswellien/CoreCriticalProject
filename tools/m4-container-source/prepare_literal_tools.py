from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
old=ROOT/'tools/m4-container-source/lift.py';new=ROOT/'tools/m4-container-source/lift_v2.py';assert not new.exists()
s=old.read_text().replace('recovery-r2','recovery-r3').replace('1f0629822493a4edbd82b25273943e8828e79576a223e63c8a669a309972e46b','b078cff8698dfbefa8d4e45a0368d4820e72c7d659520161e4316e77d3c2f26b');compile(s,str(new),'exec');new.write_text(s)
s=(ROOT/'tools/m4-mfc-native/lift.py').read_text().replace("ROOT/'reports/m4-mfc-native'/name","ROOT/'reports/m4-container-source'/name").replace("'lifts-r[1-9][0-9]*'","'provider-lifts-r[1-9][0-9]*'")
s=s.replace("ROOT/'reports/m4-strings-native/next-mfc-r1/provider-local.json','67b6e3f0402a2c148b00ed4ab120578f2dd59940b864e67c8046cef582bea9fd'","ROOT/'reports/m4-fs-next-plan/plan-r3/physical-MFC540-rows.json','0e8f1fac41ba8026d072584293af13552222642827b88efc1bb10d44e7b0877f'")
s=s.replace("for name,entry,key in [('allocate',0x5f401ea0,'ordinal823'),('free',0x5f401782,'ordinal825')]:","for name,entry,key in [('cstring',0x5f4020b4,'ordinal540'),('nil',0x5f4020c4,'nil')]:")
a="  g=graphs[key];allrows=sorted(g['instructions'],key=lambda r:r['pc'])\n  rows=[r for r in allrows if r['pc']<0x5f401ec9] if name=='allocate' else allrows\n  need(len(rows)=={'allocate':19,'free':4}[name],'Exact positive path/free source rows')"
b="  allrows=sorted(graphs,key=lambda r:r['pc']);rows=[r for r in allrows if r['pc']<0x5f4020c4]if name=='cstring'else[r for r in allrows if r['pc']>=0x5f4020c4]\n  need(len(rows)=={'cstring':8,'nil':2}[name],'Exact MFC540 constructor/getter source rows')"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("'Only original positive allocator19rows41B and free4rows12B; null allocator branch5F41B01E remains explicit unresolved TLS/handler frontier; no native execution or acceptance'","'Exact MFC540 borrowed-DWORD constructor8rows16B and getter2rows6B only; no pointee dereference, execution or constructor credit'").replace('original_rows=23,literal_source_bytes=53,unresolved_null_branch=0x5f41b01e,local_allocator_provenance_rows=33,local_allocator_provenance_bytes=85','original_rows=10,literal_source_bytes=22,borrowed_data_address=0x5f4ccb54,pointee_dereference=False')
new=ROOT/'tools/m4-container-source/provider_lift.py';assert not new.exists();compile(s,str(new),'exec');new.write_text(s)

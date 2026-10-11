"""Reattribute the additive read-only GDI identity candidate; keep prior proofs."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
old=R/'tools/m4-tree-review/review_joint138_prelaunch_v4.py'
scope={'__file__':str(old),'__name__':'materialize_current_admission'}
exec(compile(old.read_text(),str(old),'exec'),scope)
t=scope['source']
for a,b in [
 ('d20bd38e5c4f8021e204808e37c4ef752b21053210b493bdad495bd3c4f7c7aa','ea6c0f3713796e85042039c8af7cf36f0b9faee7035cdf511be1af000023d7ca'),
 ('b4cbd387ba718b52a900c5ff527749829f1936706c1b49c9e3a79a9765042ab6','ddef4da1943c6285bd462158da0e7360dcbf6a3bab40efe2247d7dea6e7c985a'),
 ("folder=R/'reports/m4-joint-startup138/preparation-r2'","folder=R/'reports/m4-joint-startup138/preparation-r3'"),
 ('reports/m4-joint-startup138/build-r3/','reports/m4-joint-startup138/build-r4/'),
 ('reports/m4-joint-startup138/admission-map-r1/report.json','reports/m4-joint-startup138/admission-map-r2/report.json'),
 ('b096a804adf5dcb6567d092f27dfa0cd4661a446e7f76b198d037941fa89e91f','bf63bb975fb4a4e70586d7a700c152a8f244a305f0eaea9eaaf2cbf6c431fd11')]:
 assert a in t,a;t=t.replace(a,b)
marker="  source=read(R/'reports/m4-tree-review/widget138-component-source-r2/report.json'"
at=t.index(marker)
t=t[:at]+"  read(R/'reports/m4-tree-review/joint138-prelaunch-r4/report.json','8ab3fb5715d92bc885c9334050aa6d9857fa794a7a6eae96a5cb1e3dd857b2a2')\n  read(R/'reports/m4-tree-review/joint138-gdi-source-r2/report.json','868e29b9afe87cd131b08c15de63fe01fa476b5034c24cd9789fd6e6ca49788a')\n"+t[at:]
a="or n.startswith('?borrow_widget_onexit@')";assert t.count(a)==1
t=t.replace(a,"or n.startswith('?borrow_widget_onexit@')or 'observe_gdi_identity'in n or n.startswith('?provider_identity@')")
anchor="   # Literal archive member provenance is byte exact, not a basename assertion."
assert t.count(anchor)==1
unwind='''   # Current complete unwind attribution for unchanged assembly wrappers.
   for n in ('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call'):
    q,raw,rels,sections=definitions[n];assert len(candidates[n])==1
    sy,se=C.parse(q.read_bytes());d=N.directories(image)[3];entries=list(struct.iter_unpack('<3I',N.image_bytes(image,image.image_base+d[0],d[1])))
    address=candidates[n][0][0];actual=[e for e in entries if image.image_base+e[0]==address];assert len(actual)==1 and image.image_base+actual[0][1]==address+len(raw)
    pdata=se[5]['bytes'];records=list(struct.iter_unpack('<3I',pdata));labels=[s for s in sy.values()if s['name']==n];assert len(labels)==1;u=[e for e in records if e[0]==labels[0]['value']];assert len(u)==1
    offset=u[0][2];data=se[4]['bytes'];next_offsets=[e[2]for e in records if e[2]>offset];end=min(next_offsets,default=len(data));assert N.image_bytes(image,image.image_base+actual[0][2],end-offset)==data[offset:end]
    counts['whole_current_ASM_unwind_relations']+=1
'''
t=t.replace(anchor,unwind+anchor)
t=t.replace("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch.py');", "  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v3.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v4.py');pin(R/'tools/m4-joint-startup138/run_v2.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())

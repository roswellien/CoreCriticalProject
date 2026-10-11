"""Derive full125 raw observer gate with separate repeated-tree helper."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def one(s,a,b):
    assert s.count(a)==1,'One exact reviewed validator change '+a[:80];return s.replace(a,b,1)
def main():
    old=ROOT/'tools/m4-lockit-original/validate_original_v2.py';s=old.read_text()
    s=s.replace("BASE=ROOT/'reports/m4-lockit-original'","BASE=ROOT/'reports/m4-tree-original'")
    s=one(s,"sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage","sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage\nsys.path.insert(0,str(Path(__file__).resolve().parent));from full_tree_phase import observe as observe_tree")
    a="p=read(pin(prep/'report.json',b['preparation_sha256']));need(p['passed']and p['record_bytes']==356992 and len(p['order'])==124,'Exact original124 ABI/order')"
    b="p=read(pin(prep/'report.json',b['preparation_sha256']));need(p['passed']and p['record_bytes']==356992 and p['original_roots']==125,'Exact original125 ABI/order');oldmeta=read(pin(ROOT/'reports/m4-lockit-original/original-preparation-r4/report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b'));\n  for key in ('genuine_DllMain_bootstrap_pages','Lockit_roots','Lockit_allocations'):p[key]=oldmeta[key]\n  p['order']=read(prep/'selected-order.json');need(len(p['order'])==125 and [r['entry'] for r in p['order'] if r['entry']!=0x4b7f70]==[r['entry'] for r in oldmeta['order']],'Exact retained124 relative order plus physical tree slot')"
    s=one(s,a,b)
    s=s.replace("b'MW4J124O'","b'MW4J125O'").replace('(1,6,124,744,43,356992)','(1,6,125,750,43,356992)')
    s=one(s,"callback_byentry={r['entry']:r['registration']['callback']for r in callback_roots};need(len(callback_byentry)==96,'96 exact recovered callbacks')","callback_byentry={r['entry']:r['registration']['callback']for r in callback_roots};callback_byentry[0x4b7f70]=0x4b7fa0;need(len(callback_byentry)==97,'97 exact recovered callbacks')")
    s=one(s,"count==(6 if entry in roots else 0)","count==(78 if entry==0x4b7f70 else 6 if entry in roots else 0)")
    s=one(s,"     if entry in roots:\n","     if entry==0x4b7f70:observe_tree(records,data,seq,phase,owners,geometry,snapshot_rows,counts,page,tid,targets,read,ROOT)\n     if entry in roots:\n")
    s=s.replace('len(owners)==8','len(owners)==15').replace("struct.pack('<96I'","struct.pack('<97I'").replace('counts[\'phases\']==744','counts[\'phases\']==750').replace("counts['Lockit_snapshots']==144","counts['Lockit_snapshots']==612").replace("counts['owners']==48","counts['owners']==90").replace("counts['new_FS_records']==72","counts['new_FS_records']==198").replace("counts['actual_API_frames']==48","counts['actual_API_frames']==204").replace('callbacks=96','callbacks=97')
    s=one(s,'pin(__file__);pin(sys.executable);passed=True',"pin(__file__);pin(ROOT/'tools/m4-tree-original/full_tree_phase.py');pin(sys.executable);passed=True")
    s=s.replace('actual original124','actual original125').replace('Actual original124','Actual original125').replace('Authentic successful phase tag','Authentic successful125 phase tag')
    s=s.replace('eight new originalowners, normal FS and96callbackregistration','15 actual original Lockit/tree owners, normal FS and97callbackregistration').replace('Complete eight owners and96 callbacks','Complete15 owners and97 callbacks').replace('per eight owner','per15 measured owners')
    out=Path(__file__).resolve().parent/'validate125.py';assert not out.exists(),'Fresh additive validator';out.write_text(s)
    print('Full125 raw observation validator prepared, not executed.')
if __name__=='__main__':main()

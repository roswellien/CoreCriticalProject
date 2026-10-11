"""Emit final ABI-safe120 readers; retain both earlier unexecuted drafts."""
from pathlib import Path
T=Path(__file__).resolve().parent
source=T/'prepare_proofs_corrected.py'
target=T/'prepare_proofs_final.py'
assert not target.exists()
s=source.read_text()
s=s.replace("Path(name).stem+'_v2.py'","Path(name).stem+'_v3.py'")
s=s.replace("re.sub(r'(?<![0-9a-f])116(?![0-9a-f])','120',s)","re.sub(r'(original|native|persistent|normal|all|complete|selected|paired|source)116',lambda m:m[1]+'120',s,flags=re.IGNORECASE)")
s=s.replace('proof-preparation-r2','proof-preparation-r3')
s=s.replace("s=s.replace('153828','166116').replace('305380','329956')\ns=s.replace(\"ROOT/'reports/m4-container-review", "s=s.replace('153828','166116').replace('305380','329956').replace('307328','331904').replace('307840','332416').replace('<88I','<92I').replace('entire35 ordinary','entire38 ordinary').replace('full37pages','full40pages')\ns=s.replace(\"ROOT/'reports/m4-container-review")
s=s.replace("s=names(s);write('compare_owned_policy.py',s)","s=one(s,\"program={r['pc']:r for r in contract['instructions']}\",\"program,_=load('full120_owned_source',ROOT/'tools/m4-next-source/game_model.py').source_program()\")\ns=names(s).replace('New120 five positive','Inherited116 five positive').replace('Native literal strlen/malloc/strcpy/result','Native literal strlen/malloc/strcpy/result in current120 sequence');write('compare_owned_policy.py',s)")
target.write_text(s)

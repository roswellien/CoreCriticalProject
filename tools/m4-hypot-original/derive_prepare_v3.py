"""Add explicit game-IAT protection restoration before actual probe use."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=R/'tools/m4-hypot-original/prepare_v2.py';q=p.with_name('prepare_v3.py');assert not q.exists();s=p.read_text();hunks=[]
 for a,b in [
 ('    *reinterpret_cast<unsigned*>(0x5bb5b0)=reinterpret_cast<unsigned>(&hypot_entry);','    {DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,PAGE_READWRITE,&prior),"Hypot game IAT observer protection");require(*reinterpret_cast<unsigned*>(0x5bb5b0)==hypot_target,"Actual named hypot target before observer");*reinterpret_cast<unsigned*>(0x5bb5b0)=reinterpret_cast<unsigned>(&hypot_entry);require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,prior,&ignored),"Hypot game IAT observer protection restored");}'),
 ('    *reinterpret_cast<unsigned*>(0x5bb5b0)=hypot_target;','    {DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,PAGE_READWRITE,&prior),"Hypot game IAT restoration protection");require(*reinterpret_cast<unsigned*>(0x5bb5b0)==reinterpret_cast<unsigned>(&hypot_entry),"Declared hypot observer before restoration");*reinterpret_cast<unsigned*>(0x5bb5b0)=hypot_target;require(VirtualProtect(reinterpret_cast<void*>(0x5bb5b0),4,prior,&ignored),"Hypot named game IAT restored protection");}'),
 ("text(R/'tools/m4-hypot-original/hypot_observer.hpp')","text(R/'tools/m4-hypot-original/hypot_observer_v2.hpp')"),
 ("pin(R/'tools/m4-hypot-original/derive_prepare_v2.py')","pin(R/'tools/m4-hypot-original/derive_prepare_v2.py');pin(R/'tools/m4-hypot-original/prepare_v2.py');pin(R/'tools/m4-hypot-original/derive_prepare_v3.py')")]:
  assert s.count(a)==1,a;s=s.replace(a,b);hunks.append(dict(old=a,new=b))
 ast.parse(s);q.write_text(s)
 op=p.with_name('hypot_observer.hpp');n=op.with_name('hypot_observer_v2.hpp');assert not n.exists();a=op.read_text();assert a.count('s.header[9]=GetLastError()')==1;n.write_text(a.replace('s.header[9]=GetLastError()','s.header[9]=saved_error'))
 out=R/'reports/m4-hypot-original/preparation-derivation-r2';assert not out.exists();out.mkdir(parents=True);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n')
 paths=[p,q,op,n,hp,Path(__file__),R/'reports/m4-hypot-original/prefix-preparation-r1/report.json'];z=out/'report.json';z.write_text(json.dumps(dict(passed=True,scope='Additive explicit read-only game IAT installer/restorer protection and genuine saved incoming LastError scalar; no machine execution',capture_reader_opened=False,files={str(x.resolve()):sha(x)for x in paths}),indent=2)+'\n');print(sha(z))
if __name__=='__main__':main()

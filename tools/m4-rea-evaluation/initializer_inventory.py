"""Exact original initializer table for Ghidra analysis seeds; no execution credit."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
GAME_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
def main(out):
 out=Path(out).resolve();assert out.parent==ROOT/'reports/m4-rea-evaluation' and not out.exists()
 game=ROOT/'MW3/Mech3.exe';raw=game.read_bytes();assert hashlib.sha256(raw).hexdigest()==GAME_SHA
 p=PEImage(raw);offset,_=p.rva_range(0x5e0000-p.image_base,0x244);table=raw[offset:offset+0x244];values=struct.unpack('<145I',table)
 roots=[dict(slot=0x5e0000+4*i,entry=a)for i,a in enumerate(values)if a];assert len(roots)==144 and len(set(r['entry']for r in roots))==144
 files={str(q.resolve()):hashlib.sha256(q.read_bytes()).hexdigest()for q in(game,Path(__file__),ROOT/'tools/analysis/pe.py')}
 data=dict(passed=True,scope='Original initializer table as static Ghidra function-entry seeds only',game=str(game),game_sha256=GAME_SHA,table_start=0x5e0000,table_end=0x5e0244,table_file_offset=offset,table_bytes_hex=table.hex(),table_sha256=hashlib.sha256(table).hexdigest(),slots=145,nonzero_entries=144,zero_slots=[0x5e0000+4*i for i,a in enumerate(values)if not a],roots=roots,files=files,native_executed=False,initializer_credit=False)
 out.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),initializer_seeds=len(roots))))
if __name__=='__main__':main(sys.argv[1])

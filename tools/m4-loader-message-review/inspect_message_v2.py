"""Fresh physical review correctly derives each variant's literal table bound."""
from pathlib import Path
p=Path(__file__).with_name('inspect_message.py');s=p.read_text();changes=[
 ('physical-r1','physical-r2'),
 ("relocation_sites={r['va']for r in relocations};table=[]","relocation_sites={r['va']for r in relocations};table=[]\n  span=struct.unpack_from('<I',bytes.fromhex(rows[base+0x1003]['bytes']),1)[0];table_end=base+0x3010+span;count=span//8\n  need(span%8==0 and struct.unpack_from('<I',bytes.fromhex(rows[base+0x1134]['bytes']),2)[0]==table_end,'Two independent whole literal table bounds')"),
 ('range(base+0x3010,base+0x6158,8)','range(base+0x3010,table_end,8)'),
 ("need(len(table)==1577 and len({r['name']for r in table})==1577,'Finite unique physical message table')","need(len(table)==count and len({r['name']for r in table})==count,'Finite unique physical message table');need(count==(1577 if label=='current'else1540),'Exact variant-specific physical table population')"),
 ('bytes_va(base+0x3010,1577*8)','bytes_va(base+0x3010,span)'),
 ('bytes_va(base+0x3000,45776)',"bytes_va(base+0x3000,next(x['virtual_size']for x in image.sections if x['name']=='.data'))")]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'))

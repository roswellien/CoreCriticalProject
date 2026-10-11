from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=T/'compare_source.py';s=p.read_text();old="  teb_base=w(raw('phase/0/13/TEB-before-base.bin'))[0];"
new="""  # Two new immutable RX pages are not part of the inherited46 semantic
  # endpoint pages. Their input comes from the exact physically admitted pack;
  # current worker checks every whole source span before and after execution.
  pack=pin(Path(build['preparation'])/'pages.bin',prep['pack_sha256']).read_bytes();eq(pack[:8],b'MW4J124P','Physical source pack tag');n=w(pack,8)[0];eq(len(pack),12+n*4104,'Exact sparsepack geometry');packed={}
  for i in range(n):
   off=12+i*4104;address,permission=w(pack,off,2);packed[address]=(permission,pack[off+8:off+4104])
  missing={row['pc']&~4095 for row in program.values()if(row['pc']&~4095)not in memory};eq(missing,{0x5ab000,0x5ae000},'Only new immutable gamecode pages absent from inherited semantic inventory')
  for address in sorted(missing):
   permission,data_=packed[address];eq(permission,1,'Immutable executable sourcepage');eq(len(data_),4096,'Whole exact sourcepage');memory[address]=bytearray(data_);counts['physical_pack_readonly_source_code_input_pages']+=1
  pin(R/'tools/m4-mfc1168-connected-original/compare_source.py');pin(R/'tools/m4-mfc1168-connected-original/derive_compare_v2.py')
  teb_base=w(raw('phase/0/13/TEB-before-base.bin'))[0];"""
if s.count(old)!=1:raise ValueError('Exact one source input insertion')
s=s.replace(old,new);out=T/'compare_source_v2.py'
if out.exists():raise ValueError('Fresh derivative')
out.write_text(s);print(sha(out))

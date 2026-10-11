"""Additive exact logical identity names and literal raw FS-byte checks."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-fs-control-audit/audit_v2.py';s=p.read_text()
a="path=a.data(stem+('-path.bin'if custom else'-module-path.bin'))"
b="path=a.data((stem.removesuffix('-after')+'-path.bin')if custom else(stem+'-module-path.bin'))";assert s.count(a)==1;s=s.replace(a,b)
a="digest=a.data(stem+('-sha.bin'if custom else'-module-sha.bin'))";b="digest=a.data((stem.removesuffix('-after')+'-sha.bin')if custom else(stem+'-module-sha.bin'))";assert s.count(a)==1;s=s.replace(a,b)
assert s.count('p[3]==0x7802e088')==1;s=s.replace('p[3]==0x7802e088','p[3]==0x7802e094')
a="     need(tib[0]==tib[4]==0x7ffde000"
insert="""     record_rows=rows(a.data(live+'fs-record-bytes.bin'),16)
     for raw in record_rows:
      need(raw[0]==1 and record_rows[raw[1]]==raw and raw[4]in(81,84)and raw[7]==12 and raw[11]<=len(source),'True indexed full source record observation')
      rebuilt={}
      for pc,address,value,width,writing in source[:raw[11]]:
       if writing:
        for i in range(width):
         if raw[6]<=address+i<raw[6]+12:rebuilt[address+i-raw[6]]=(value>>(i*8))&255
      need(set(rebuilt)==set(range(12))and bytes(rebuilt[i]for i in range(12))==struct.pack('<3I',*raw[8:11]),'Every raw twelve-byte FS observation equals latest literal committed stack bytes, including real scope transitions')
      counts['complete12B_FS_source_observations']+=1
"""
assert s.count(a)==1;s=s.replace(a,insert+a)
a="'Nested inner restore genuinely leaves its same owned outer frame active')"
b=a+"\n       need(stack[parent[9]-0x20001000:parent[9]-0x20001000+12]==struct.pack('<3I',parent[8],parent[10],0xffffffff)and not any(pc==0x4d491a and writing for pc,_,_,_,writing in source),'Whole twelve-byte outer record stays unchanged only during actual inner interval')"
assert s.count(a)==1;s=s.replace(a,b)
a="      if point>=86:"
b="      if case==20:need((0x4d491a,f[9]+8,0,4,1)in source and struct.unpack_from('<I',stack,f[9]-0x20001000+8)[0]==0,'Literal post-inner outer scope change precedes final restore refusal')\n"+a
assert s.count(a)==1;s=s.replace(a,b)
t=p.with_name('audit_v3.py');assert not t.exists();t.write_text(s)

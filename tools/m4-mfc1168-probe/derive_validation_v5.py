"""Close all imported decoder modules and actual system provider identities.

Preserves the executed v4 proof; the next bounded run authenticates complete
reached physical byte spans and compares whole source-derived loaded pages.
"""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-mfc1168-probe/validate_v4.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='abdae81be1ba496a76c6613c8104804e83175fd4ae1a41b7f2d631f7e55dba81'
s=p.read_text(encoding='utf-8-sig')
a="  m=Literal(state,raw(p/'FX-before.bin'),struct.pack('<10I',*first),memory,program=program,callbacks={});domain={};API_index=0;flag_rows=[]"
assert s.count(a)==1
s=s.replace(a,a+"\n  for pc in set(f['PC']for f in facts):eq(m.bytes(pc,rows[pc]['width']),bytes.fromhex(rows[pc]['bytes_hex']),'Entire genuine reached instruction physical span')")
a="  callbacks=(0x5f4053fe,0x5f40b293);"
assert s.count(a)==1
s=s.replace(a,"  for module in('MFC','CRT'):\n   for page,protect,type_,owner in struct.iter_unpack('<4I',raw(p/f'BEFORE/{module}/metadata.bin')):eq(m.bytes(page,4096),raw(p/f'AFTER/{module}/{page}.bin'),'Complete source-derived loaded provider page');counts['literal_whole_loaded_module_pages']+=1\n  eq(m.bytes(0x736000,4096),raw(p/'AFTER/game/7561216.bin'),'Entire source-derived fixed game object page')\n"+a)
a="  pin(__file__);pin(sys.executable);passed=True"
assert s.count(a)==1
s=s.replace(a,"  for provider in named:pin(provider['module_path'],provider['module_sha256'])\n  for module in list(sys.modules.values()):\n   origin=getattr(module,'__file__',None)\n   if origin and Path(origin).resolve().is_relative_to(R):pin(origin)\n  pin(R/'tools/m4-mfc1168-probe/derive_validation_v5.py');pin(__file__);pin(sys.executable);passed=True")
out=R/'tools/m4-mfc1168-probe/validate_v5.py';assert not out.exists();out.write_text(s,encoding='utf-8');print(hashlib.sha256(out.read_bytes()).hexdigest())

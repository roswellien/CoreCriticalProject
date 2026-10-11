"""Retain coherent complete TEB input at the authored assembly root boundary.

The earlier whole TEB observation used safe_read, whose temporary SEH frame
changed FS:[0] while copying. Preserve those observations; this additive worker
copies two actual TEB pages directly in assembly before entering guest code.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r7';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='3bed2fe6ec6f2676197b8fd7520925b9761421b197d8bc43bdd3454fa4ba507b';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'worker.cpp';s=p.read_text();a='void mixed_enter();void mixed_capture();void mixed_restore();';assert s.count(a)==1;s=s.replace(a,a+'\nunsigned mixed_teb_before_base{};unsigned char mixed_teb_before_pages[8192]{};')
 a='dump("CPU-before.bin",&mixed_before,40);';assert s.count(a)==1;s=s.replace(a,a+'dump("root-TEB-before-base.bin",&mixed_teb_before_base,4);dump("root-TEB-before-pages.bin",mixed_teb_before_pages,8192);');p.write_text(s)
 p=out/'reference_x86.asm';s=p.read_text();a='EXTERN mixed_host_esp:DWORD';assert s.count(a)==1;s=s.replace(a,a+'\nEXTERN mixed_teb_before_base:DWORD\nEXTERN mixed_teb_before_pages:BYTE')
 a=' fxsave mixed_host_fx\n';assert s.count(a)==1;s=s.replace(a,a+' ; Coherent untouched actual TEB input before any guest source instruction.\n mov esi,DWORD PTR fs:[18h]\n and esi,0fffff000h\n mov mixed_teb_before_base,esi\n mov edi,OFFSET mixed_teb_before_pages\n mov ecx,2048\n cld\n rep movsd\n');p.write_text(s)
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Coherent actual full8192B TEB snapshot at assembly root entry, before guest source instructions. Earlier safe_read page carries are preserved separately; no FS/TLS/locale source seed.',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])

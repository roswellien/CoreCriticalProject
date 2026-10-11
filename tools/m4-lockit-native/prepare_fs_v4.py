"""Add the two physically observed early-FS-read prologs; preserve candidate3."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 base=ROOT/'reports/m4-lockit-native/preparation-r3'
 assert sha(base/'report.json')=='4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d'
 parent=json.loads((base/'report.json').read_bytes());assert parent['passed']
 out=ROOT/'reports/m4-lockit-native'/name;assert not out.exists();out.mkdir(parents=True)
 pins=dict(parent['files']);pins[str(base/'report.json')]=sha(base/'report.json')
 for p in base.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):
   assert sha(p)==pins[str(p.resolve())];(out/p.name).write_bytes(p.read_bytes())
 path=out/'fs_operations.inc';s=path.read_text()
 before=''' const auto&call=calls_.back();const auto frame=state.gpr.rsp.dword+8;
 if(frame!=call.frame||runtime.memory().load<unsigned>({frame})!=call.return_pc||
    runtime.memory().load<unsigned>({frame-8})!=spec->handler||runtime.memory().load<unsigned>({frame-4})!=UINT32_MAX)'''
 after=''' const auto&call=calls_.back();
 // These two exact prologs read FS before committing their two literal pushes.
 // Their complete handler/scope/predecessor bytes are checked at installation.
 const bool early=(spec->read==0x4125a0U||spec->read==0x500cd0U)&&spec->entry==spec->read;
 const auto frame=state.gpr.rsp.dword+(early?0:8);
 if(frame!=call.frame||runtime.memory().load<unsigned>({frame})!=call.return_pc||
    (!early&&(runtime.memory().load<unsigned>({frame-8})!=spec->handler||runtime.memory().load<unsigned>({frame-4})!=UINT32_MAX)))'''
 assert s.count(before)==1;s=s.replace(before,after);path.write_text(s)
 pins[str(Path(__file__).resolve())]=sha(__file__)
 for p in out.iterdir():
  if p.is_file():pins[str(p.resolve())]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
 report=parent|dict(scope='Candidate124 with exact two early-FS-read prologs; complete twelve-byte installation/restoration guard retained; execution pending',native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),previous_native_preparation=str(base/'report.json'),previous_native_preparation_sha256=sha(base/'report.json'),early_FS_read_PCs=[0x4125a0,0x500cd0],complete_FS_installation_guard_unchanged=True,files=pins|{str((out/'pins.json').resolve()):sha(out/'pins.json')})
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])

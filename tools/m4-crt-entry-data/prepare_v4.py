"""Add literal complete entry source captures to every existing checkpoint."""
import hashlib,json,pathlib,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-data'
def sha(p):
 with pathlib.Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
 out=pathlib.Path(out).resolve();assert out.parent==BASE and not out.exists();previous=BASE/'preparation-r3';files={}
 for p,h in json.loads((previous/'pins.json').read_text())['files'].items():assert sha(p)==h,p;files[p]=h
 s=(previous/'observations.hpp').read_text();a='auto phase=directory/name;require(std::filesystem::create_directory(phase),"Fresh phase directory");'
 assert s.count(a)==1;s=s.replace(a,a+'std::array<std::byte,430>source{};r.memory().read({entry},source);fresh_output(phase/"entry-source.bin",source);')
 out.mkdir()
 for name in ('composition.cpp','seed.hpp','main_v2.inc'):shutil.copyfile(previous/name,out/name)
 shutil.copyfile(previous/'observations.hpp',out/'observations-ancestor.hpp');(out/'observations.hpp').write_text(s)
 report=dict(passed=True,State_bytes=3504,State_reseed_after_writer=False,scope='Additive literal source checkpoint supplement; same execution/control semantics',
  previous_source_sha256=sha(previous/'composition.cpp'),source_sha256=sha(out/'composition.cpp'),
  entry_source_checkpoint_bytes=430,actual_control7_entry_DWORD_retained=True,
  permission_controls='Declared harness region/permission operations and actual observed causal faults; GuestMemory has no public permission query',
  native_executed=False,original_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for p in out.iterdir():files[str(p)]=sha(p)
 for p in (pathlib.Path(__file__).resolve(),previous/'report.json',previous/'pins.json'):files[str(p)]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])

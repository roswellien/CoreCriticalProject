"""Replace an incorrect zero-IAT assumption with exact owned image metadata."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'reports/m4-crt-entry/prefix-preparation-r2';OUT=ROOT/'reports/m4-crt-entry/prefix-preparation-r3'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not OUT.exists();OUT.mkdir(parents=True)
source=OLD/'prefix.cpp';assert sha(source)=='23b3540d937a1c6f2f2455a61e6e95f02b7fd905f8f959e5f60b48be755d2e22'
(OUT/'prefix.cpp.ancestor').write_bytes(source.read_bytes());text=source.read_text()
a=' std::vector<Event>events_;bool running_{};';assert text.count(a)==1;text=text.replace(a,' std::vector<Event>events_;bool running_{};unsigned data_iat_{};')
a='  for(unsigned i=0;i<3504;++i)';assert text.count(a)==1;text=text.replace(a,'  unsigned owners=0;for(const auto&i:r.image_metadata().imports)if(r.image_metadata().image_base+i.iat_rva==0x5bb508){require(i.name&&*i.name=="_adjust_fdiv"&&i.library=="MSVCRT.dll","Actual FDIV data import owner");data_iat_=i.original_iat_value;++owners;}require(owners==1&&r.memory().load<unsigned>({0x5bb508})==data_iat_,"Exact source FDIV raw IAT identity");\n'+a)
a='s_.gpr.rip.dword==0x5ac408&&v==0';assert text.count(a)==1;text=text.replace(a,'s_.gpr.rip.dword==0x5ac408&&v==data_iat_')
new=OUT/'prefix.cpp';new.write_text(text)
builder=ROOT/'tools/m4-crt-entry/build-prefix-v2.ps1';(OUT/'build-prefix-v2.ps1.ancestor').write_bytes(builder.read_bytes());text=builder.read_text().replace("prefix-build-r2'","prefix-build-r3'").replace('prefix-preparation-r2/prefix.cpp','prefix-preparation-r3/prefix.cpp').replace(sha(source),sha(new))
target=ROOT/'tools/m4-crt-entry/build-prefix-v3.ps1';assert not target.exists();target.write_text(text)
files={str(p):sha(p)for p in(source,new,builder,target,OUT/'prefix.cpp.ancestor',OUT/'build-prefix-v2.ps1.ancestor',OLD/'report.json',ROOT/'reports/m4-crt-entry/prefix-build-r2/build.json',ROOT/'reports/m4-crt-entry/prefix-build-r2/native-O0.log',Path(__file__))}
(OUT/'report.json').write_text(json.dumps(dict(passed=True,scope='Additive correction to exact raw import identity; previous zero assumption failed before reaching expected missing-data boundary',files=files,actual_file_import_is_lookup_RVA=True,initialized_provider_DWORD_and_raw_game_IAT_are_distinct=True,production_change='Use hash-admitted image import owner/original DWORD; no guessed IAT value or pointer substitution',original_executed=False,full_CRT=False,whole_M4_complete=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=sha(OUT/'report.json'),source_sha256=sha(new))))

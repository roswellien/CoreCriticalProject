"""Retain original5 and compare loaded/copy physical file identities exactly."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2];OLD=R/'reports/m4-version-source/original-preparation-r5'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 old=json.loads(pin(OLD/'report.json','149a328436631f8d7f7f579629deb2a8367bd3d1e76296cbaaaed14385c6fc30').read_bytes());assert old['passed']
 for p,h in old['files'].items():pin(p,h)
 pin(R/'reports/m4-version-source/original-build-r5/build.json','85872a4a2a3932d1c2ab05c28aaad4e8b14a59d2137c9ff8b24e1dc45b75ed87');out.mkdir(parents=True);relations=[]
 for p in OLD.iterdir():
  if p.is_file()and p.name not in('report.json','pins.json'):
   q=out/p.name;shutil.copyfile(p,q);relations.append(dict(parent=str(p),child=str(q),sha256=sha(q),unchanged=True))
 q=out/'version_provider_isolation.hpp';s=q.read_text()
 a='static std::wstring version_isolated_VERSION_path,version_isolated_CRT_path;'
 b=a+'''
static std::array<std::array<std::uint64_t,7>,4>version_provider_file_IDs{};
static std::array<std::uint64_t,7>version_provider_file_ID(const std::filesystem::path&p){
 struct File {HANDLE h{INVALID_HANDLE_VALUE};~File(){if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);}}f;
 f.h=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);require(f.h!=INVALID_HANDLE_VALUE,"Actual VERSION provider physical file opened for identity");
 BY_HANDLE_FILE_INFORMATION i{};require(GetFileInformationByHandle(f.h,&i),"Whole actual VERSION provider physical file identity");return {i.dwVolumeSerialNumber,i.nFileIndexHigh,i.nFileIndexLow,i.nFileSizeHigh,i.nFileSizeLow,i.ftLastWriteTime.dwHighDateTime,i.ftLastWriteTime.dwLowDateTime};
}
'''
 assert s.count(a)==1;s=s.replace(a,b,1)
 a='require(!_wcsicmp(version_isolated_CRT_path.c_str(),CRT_path.c_str())&&!_wcsicmp(version_isolated_VERSION_path.c_str(),VERSION_path.c_str())&&version_isolated_crt!=old,"Actual loaded private system32 DLL paths and distinct legacy CRT owner");'
 b='''version_provider_file_IDs={version_provider_file_ID(std::filesystem::path(version_isolated_VERSION_path)),version_provider_file_ID(VERSION_path),version_provider_file_ID(std::filesystem::path(version_isolated_CRT_path)),version_provider_file_ID(CRT_path)};
 require(version_provider_file_IDs[0]==version_provider_file_IDs[1]&&version_provider_file_IDs[2]==version_provider_file_IDs[3]&&std::filesystem::equivalent(std::filesystem::path(version_isolated_VERSION_path),VERSION_path)&&std::filesystem::equivalent(std::filesystem::path(version_isolated_CRT_path),CRT_path)&&version_isolated_crt!=old,"Actual loaded/copy same physical file IDs and exact paths with distinct legacy CRT owner");'''
 assert s.count(a)==1;s=s.replace(a,b,1)
 a='out.append("version-provider/setup.bin",version_provider_setup.data(),sizeof(version_provider_setup));'
 b=a+'out.append("version-provider/file-IDs.bin",version_provider_file_IDs.data(),sizeof(version_provider_file_IDs));'
 assert s.count(a)==1;s=s.replace(a,b,1);q.write_text(s)
 for relation in relations:
  if Path(relation['child']).name=='version_provider_isolation.hpp':relation.update(unchanged=False,parent_sha256=sha(OLD/'version_provider_isolation.hpp'),sha256=sha(q),exact_changes=['actual loaded and expected copies each record whole seven-Q BY_HANDLE file identity','same whole file IDs plus independent filesystem equivalence replace spelling comparison','whole four physical file-ID records emitted'])
 c=json.loads((out/'contracts.json').read_bytes());c.update(actual_loaded_and_expected_provider_whole_file_IDs=True,independent_same_physical_provider_file_equivalence=True,raw_loaded_provider_paths_retained=True);(out/'contracts.json').write_text(json.dumps(c,indent=2)+'\n')
 pin(__file__)
 for p in out.iterdir():
  if p.is_file():pin(p)
 d={k:v for k,v in old.items()if k not in('files','source_relations','parent_preparation_sha256','scope')};d.update(passed=True,scope='Original6 retains original5 isolation and source guards; loaded provider/copy equality proven by whole physical file IDs and independent file equivalence rather than path spelling; build only',parent_preparation_sha256=sha(OLD/'report.json'),source_relations=relations,actual_provider_file_identity_bytes=224,raw_loaded_provider_paths_retained=True,original_executed=False,native_executed=False,archive_reader_opened=False,files=pins)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),executed=False)))
if __name__=='__main__':main(sys.argv[1])

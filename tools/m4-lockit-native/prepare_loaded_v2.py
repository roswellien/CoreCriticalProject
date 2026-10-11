"""Bind current genuine124 loader pages; retain candidate preparation1 unchanged."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(bootstrap_report,bootstrap_sha,name):
 bp=Path(bootstrap_report).resolve();assert sha(bp)==bootstrap_sha;b=json.loads(bp.read_bytes());assert b['passed']
 base=ROOT/'reports/m4-lockit-native/preparation-r1';assert sha(base/'report.json')=='b2a1001d517080421d2ce520a874da02d83f099f6694a2c9aca0b7a4faa7a4dd';parent=json.loads((base/'report.json').read_bytes());assert parent['passed']
 out=ROOT/'reports/m4-lockit-native'/name;assert not out.exists();out.mkdir(parents=True)
 pins=dict(parent['files']);pins[str(base/'report.json')]=sha(base/'report.json');pins[str(bp)]=bootstrap_sha
 for p,h in b['files'].items():
  assert p not in pins or pins[p]==h
  if p not in pins:assert sha(p)==h
  pins[p]=h
 # The extraction receipt names the exact canonical original bootstrap pages.
 assert b['record_bytes']==356992 and b['observed_pages']==43 and b['counts']['phases']==744 and b['initialized_state']==2 and not b['state_seeded']
 data_path=bp.parent/'post-DllMain-78145000-page.bin';iat_path=bp.parent/'post-DllMain-78146000-page.bin';assert sha(data_path)==b['files'][str(data_path)] and sha(iat_path)==b['files'][str(iat_path)];data=data_path.read_bytes();iat=iat_path.read_bytes();assert len(data)==len(iat)==4096 and int.from_bytes(data[0x658:0x65c],'little')==2
 imports={i['symbol']:i for i in json.loads((bp.parent/'loaded-imports.json').read_bytes())};enter=int(imports['EnterCriticalSection']['target']);leave=int(imports['LeaveCriticalSection']['target']);assert imports['EnterCriticalSection']['cell']==0x78146198 and imports['LeaveCriticalSection']['cell']==0x78146184 and int.from_bytes(iat[0x198:0x19c],'little')==enter and int.from_bytes(iat[0x184:0x188],'little')==leave
 for p in base.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):
   assert sha(p)==parent['files'][str(p.resolve())];(out/p.name).write_bytes(p.read_bytes())
 p=out/'lockit_contract.inc';s=p.read_text();a=s.index('const std::array<std::byte,4096>lockit_loaded_page{');e=s.index(';',a);s=s[:a]+'const std::array<std::byte,4096>lockit_loaded_page{'+','.join('std::byte{'+str(v)+'}'for v in data)+'};\nconst std::array<std::byte,4096>lockit_loaded_iat_page{'+','.join('std::byte{'+str(v)+'}'for v in iat)+'}'+s[e:];s=one(s,'0x78146198,0x866ae,1','0x78146198,'+str(enter)+',1');s=one(s,'0x78146184,0x86718,1','0x78146184,'+str(leave)+',1');p.write_text(s)
 p=out/'session_impl.inc';s=p.read_text();s=one(s,'p.address==0x78145000?lb::lockit_loaded_page:(p.address==0x7810a000||p.address==0x78146000)?lockit_raw_page','p.address==0x78145000?lb::lockit_loaded_page:p.address==0x78146000?lb::lockit_loaded_iat_page:p.address==0x7810a000?lockit_raw_page');p.write_text(s)
 p=out/'lockit_operations.inc';s=p.read_text();s=one(s,'native_apis_.back().outputs.push_back(bytes);preflight_write','native_apis_.back().words[13]=24;native_apis_.back().words[29]=1;native_apis_.back().words[30]=1;native_apis_.back().outputs.push_back(bytes);preflight_write');p.write_text(s)
 pins[str(Path(__file__).resolve())]=sha(__file__)
 for p in out.iterdir():
  if p.is_file():pins[str(p.resolve())]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');files=pins|{str((out/'pins.json').resolve()):sha(out/'pins.json')}
 report=parent|dict(scope='Current original124 loaded whole-page inputs and exact named Lockit API/resource derivative; combinednative/source/controls acceptance pending',native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),loaded_input_page=str(data_path),loaded_input_page_sha256=sha(data_path),loaded_IAT_page=str(iat_path),loaded_IAT_page_sha256=sha(iat_path),loaded_original_bootstrap_report=str(bp),loaded_original_bootstrap_sha256=bootstrap_sha,named_original_API_targets=dict(EnterCriticalSection=enter,LeaveCriticalSection=leave),guest_CS_semantic_outputs=24,guest_CS_native_opaque_copy=False,native_DllMain_executed=False,inherited_physical_hashes_bound_to_preparation1=True,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])

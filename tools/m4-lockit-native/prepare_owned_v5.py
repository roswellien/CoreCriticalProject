"""Admit literal new FS-owner accesses/publications with unchanged requested bounds."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def append_array(s,name,rows):
 begin=s.index('constexpr '+name+'[]{');end=s.index('};',begin)
 return s[:end]+''.join('{'+','.join(map(str,row))+'},\n' for row in rows)+s[end:]
def main(contract_report,expected,name):
 rp=Path(contract_report).resolve();assert sha(rp)==expected;contract=json.loads(rp.read_bytes());assert contract['passed']
 cp=Path(contract['contracts']);assert sha(cp)==contract['contracts_sha256'];spec=json.loads(cp.read_bytes())
 assert len(spec['fs_owned_accesses'])==32 and len(spec['fs_inputs'])==8
 assert {r[0] for r in spec['fs_owned_accesses']}=={0x411010,0x4dc140,0x500660,0x5968f0}
 assert all(r[2:4]==[1,4] and r[0]==r[4] for r in spec['fs_owned_accesses'])
 base=ROOT/'reports/m4-lockit-native/preparation-r4'
 assert sha(base/'report.json')=='f090bad6da0e6e28090218f04e9f98ebe358e31ac6901a266d8e29ffc45ff608'
 parent=json.loads((base/'report.json').read_bytes());assert parent['passed']
 out=ROOT/'reports/m4-lockit-native'/name;assert not out.exists();out.mkdir(parents=True)
 pins=dict(parent['files']);pins[str(base/'report.json')]=sha(base/'report.json')
 for p,h in contract['files'].items():assert p not in pins or pins[p]==h;assert sha(p)==h;pins[p]=h
 pins[str(rp)]=expected;pins[str(cp)]=sha(cp)
 for p in base.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):
   assert sha(p)==parent['files'][str(p.resolve())];(out/p.name).write_bytes(p.read_bytes())
 p=out/'fs_contract.inc';s=p.read_text();s=append_array(s,'FsInput fs_inputs',spec['fs_inputs']);s=append_array(s,'FsOwnedAccess fs_owned_accesses',spec['fs_owned_accesses']);p.write_text(s)
 p=out/'lockit_contract.inc';s=p.read_text();start=s.index('constexpr MfcRootInput lockit_mfc_inputs[]{');end=s.index('};',start);lines=s[start:end].splitlines();assert len(lines)==9
 # FS owns every publication, so the generic MFC layer must not count it again.
 for i in range(1,len(lines)):
  values=lines[i].strip().strip('{},').split(',');assert len(values)==5;values[-1]='0';lines[i]='{'+','.join(values)+'},'
 s=s[:start]+'\n'.join(lines)+'\n'+s[end:];p.write_text(s)
 pins[str(Path(__file__).resolve())]=sha(__file__)
 for p in out.iterdir():
  if p.is_file():pins[str(p.resolve())]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
 result=parent|dict(scope='Candidate124 exact32 new requested-bound source owner accesses and eight FS-owned publications; full execution/controls acceptance pending',native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),previous_native_preparation_sha256=sha(base/'report.json'),owner_contract_report=str(rp),owner_contract_report_sha256=expected,new_FS_owned_accesses=32,new_FS_owned_publications=8,generic_MFC_publication_count_for_new_sites=0,files=pins|{str((out/'pins.json').resolve()):sha(out/'pins.json')})
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])

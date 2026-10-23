"""ROOT current physical Lockit contract/depth review, no generation relaxation."""
from pathlib import Path
import ast,hashlib,json,re
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';p=base/'ROOT-native36-admission-r7/report.json'
 assert sha(p)=='1c4e192972561c37f570f49abea11de526550f4fc8034b455f7acb820e182f02'
 A=json.loads(p.read_bytes());pins=dict(A['files']);pins[str(p)]=sha(p)
 prep=base/'native-Lockit-contract-preparation-r1/report.json';assert sha(prep)=='e52991548832713a380f94e058f909d46036211b4a91621881fcd8058b62be50'
 F=json.loads(prep.read_bytes());assert F['prepared'] and not F['source_executed'] and not F['reader_opened'];pins[str(prep)]=sha(prep)
 for path,h in F['files'].items():assert pins.setdefault(path,h)==h
 diag=base/'native-Lockit-contract-diagnostic-r1/report.json';assert sha(diag)=='e8c79f7fc7b1184a14b491e8d0b563dbb233a29bf6dc44fa6458adfe0fc2aa4c'
 D=json.loads(diag.read_bytes());pins[str(diag)]=sha(diag)
 for path,h in D['files'].items():assert pins.setdefault(path,h)==h
 for path,h in pins.items():assert sha(path)==h
 td=R/'tools/m4-startup141-paired'
 for group in json.loads((prep.parent/'exact-inverse.json').read_bytes()):
  text=(td/group['current']).read_text()
  for d in reversed(group['replacements']):
   assert text.count(d['new'])==d['new_count'];text=text.replace(d['new'],d['old'])
  assert text==(td/group['parent']).read_text();ast.parse((td/group['current']).read_text())
 pattern=r'\{\s*(0x[0-9a-fA-F]+|\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*,\s*(\d+)\s*,\s*"([A-Za-z]+)"\s*,\s*(\d+)\s*\}'
 extracted={};sp=R/'reports/m4-startup141-runway/service-preparation-r2'
 for leaf in('source_contract.inc','registry_contract.inc','lockit_contract.inc'):
  for site,slot,raw,argc,name,tail in re.findall(pattern,(sp/leaf).read_text()):
   key=str(int(site,0)if site.startswith('0x')else int(site));value=[name,int(slot,0)if slot.startswith('0x')else int(slot),int(raw,0)if raw.startswith('0x')else int(raw),int(argc),int(tail)]
   assert key not in extracted or extracted[key]==value;extracted[key]=value
 old=json.loads((base/'native-owner-metadata-preparation-r2/physical-API-contracts.json').read_bytes());new=json.loads((prep.parent/'physical-API-contracts.json').read_bytes())
 assert new==extracted and all(new[k]==v for k,v in old.items()) and set(new)-set(old)=={'2014356235','2014356318'}
 ns={};exec(compile((td/'native_owner_metadata_v8.py').read_text(),'ROOT exact Lockit metadata','exec'),ns)
 cs={};exec(compile((td/'native_owner_metadata_controls_v6.py').read_text(),'ROOT exact Lockit controls','exec'),cs)
 result=cs['controls'](ns['derive']);assert result['passed'] and result['negative_controls']==68 and len(set(result['refused']))==68
 out=base/'root-owner-metadata-controls-r4';assert not out.exists();out.mkdir();cq=out/'report.json'
 cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,exact_current_physical_contract_extraction=True,accepted_function_credit=0,files={str(td/f):sha(td/f)for f in('native_owner_metadata_v8.py','native_owner_metadata_controls_v6.py')}),indent=2)+'\n')
 pins[str(cq)]=sha(cq);pins[str(Path(__file__).resolve())]=sha(__file__)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-native36-admission-r8';assert not out.exists();out.mkdir();A.update(exact_current_Lockit_contracts_and_balanced_causal_depth_reviewed=True,Lockit_scope_does_not_increment_generation=True,files=pins)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()

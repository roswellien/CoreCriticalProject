"""Serialize proven owner/publication fields in the native struct order."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 base=ROOT/'reports/m4-lockit-source/owned-contracts-r1';p=base/'report.json';assert sha(p)=='8ca045fb36a503276b05223b4c9401792077e256dbf3c37691ecb9adb4e3a51a';d=json.loads(p.read_bytes());pins=dict(d['files']);pins[str(p)]=sha(p)
 for path,h in pins.items():assert sha(path)==h
 owned=json.loads((base/'shared-owner-accesses.json').read_bytes());inputs=json.loads((base/'allocation-inputs.json').read_bytes());contract=dict(fs_owned_accesses=[[int(r[k])for k in('root','pc','write','bytes','owner_root','owner_CALL_pc','owner_offset')]for r in owned],fs_inputs=[[int(r[k])for k in('root','CALL_pc','requested_size','object','publication','publication_PC','owner_root','owner_CALL_pc','owner_offset')]for r in inputs]);out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);p=out/'contracts.json';p.write_text(json.dumps(contract,indent=2)+'\n');pins[str(p)]=sha(p);pins[str(Path(__file__).resolve())]=sha(__file__);report=dict(passed=True,scope='Field-order serialization of exact static affine owner/publication source contract; original/runtime confirmation separate',contracts=str(p),contracts_sha256=sha(p),owned_accesses=32,publications=8,files=pins,initializer_credit=False);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),contracts_sha256=report['contracts_sha256'])))
if __name__=='__main__':main(sys.argv[1])

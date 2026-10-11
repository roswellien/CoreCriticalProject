"""Bind the dedicated refusal boundary beside the unchanged selected boundary."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 pp=R/'reports/m4-joint-startup138/controls-preparation-r1/report.json';assert sha(pp)=='b6181058d7e7dd1a8bd03dbbae87e2e35976304e541c491f803a64e5839ad564';d=json.loads(pp.read_bytes());out=pp.parent.parent/name;assert not out.exists();out.mkdir();pins=dict(d['files']);pins[str(pp.resolve())]=sha(pp);rows=[]
 for p,h in pins.items():assert Path(p).suffix.lower()not in('.mwb','.zip')and sha(p)==h
 for p in pp.parent.rglob('*'):
  if p.is_file()and p.name!='report.json':q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);b=p.read_bytes();v=b.replace(pp.parent.as_posix().encode(),out.as_posix().encode());q.write_bytes(v);rows.append(dict(source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),path_rebase=b!=v))
 p=out/'connected_hardware_boundary.s';p.write_bytes(p.read_bytes()+b'\n'+(out/'controls_hardware_boundary.s').read_bytes())
 for row in rows:row.update(current_sha256=sha(row['target']),byte_identical=sha(row['target'])==row['source_sha256']);assert row['byte_identical']or row['path_rebase']or Path(row['target']).name=='connected_hardware_boundary.s'
 generated={}
 for p in out.rglob('*'):
  if p.is_file():pins[str(p.resolve())]=sha(p);generated[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable);d.update(parent_preparation=str(pp.resolve()),parent_preparation_sha256=sha(pp),prior_copy_relations=rows,generated_sources=generated,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])

from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/authorized-io-preparation-r2';out.mkdir();files={};deltas=[]
 def pin(p):
  p=Path(p).resolve();files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
 parent=pin(R/'tools/m4-original141-tree-source/run_ordinary_v3.py');s=parent.read_text(encoding='utf-8')
 for a,b in [("gate=read(admission_path,admission_sha);", "assert admission_path==R/'reports/m4-original141-tree-source/root-source-admission-r1/report.json','Exact ROOT tree admission namespace';gate=read(admission_path,admission_sha);"),("path.parent.name.startswith(name+'-case-')and path.parent.name[len(name+'-case-'):].isdigit()and 0<=int(path.parent.name[len(name+'-case-'):])<6", "path.parent.name in {name+'-case-'+str(i)for i in range(6)}")]:
  assert s.count(a)==1;s=s.replace(a,b);deltas.append(dict(old=a,new=b))
 rev=s
 for d in reversed(deltas):assert rev.count(d['new'])==1;rev=rev.replace(d['new'],d['old'])
 assert rev==parent.read_text(encoding='utf-8');ast.parse(s);q=parent.with_name('run_ordinary_v4.py');assert not q.exists();q.write_text(s,encoding='utf-8');pin(q);pin(__file__)
 p=out/'deltas.json';p.write_text(json.dumps(deltas,indent=2)+'\n',encoding='utf-8');pin(p)
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,prepared_only=True,exact_two_delta_inverse=True,exact_admission_namespace=True,exact_six_child_output_names=True,ordinary_reader_opened=False,canonical_reader_opened=False,worker_launched=False,files=files),indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()

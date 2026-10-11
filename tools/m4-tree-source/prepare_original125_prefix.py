"""Additive six-case genuine-original tree-prefix source comparison adapter."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 base=ROOT/'tools/m4-tree-source/compare_prefix_v2.py';s=base.read_text()
 def one(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 one('def main(name,model_path):','def main(name,model_path,sequence):')
 one("ROOT/'reports/m4-tree-original/prefix-validation-r2/report.json','58e023bb24afc474b164c454bc3591bf2cd476c70b3ce90607251ea67583a920'", "ROOT/'reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'")
 one("execution=read(validation['execution_path'],validation['execution_sha256'])", "execution=read(Path(validation['execution_path'])/'report.json',validation['execution_sha256'])")
 one("owners=read(Path(validation['execution_path']).parents[1]/'prefix-validation-r2/actual-owners.json',validation['files'][str((ROOT/'reports/m4-tree-original/prefix-validation-r2/actual-owners.json').resolve())]);owner_index=[0]", "geometry_path=ROOT/'reports/m4-tree-original/original125-validation-r1/allocation-geometry.json';geometry=read(geometry_path,validation['files'][str(geometry_path.resolve())]);owners=[dict(row,actual_API_index=row['API_index'],final_hex=row['actual_final_hex'])for row in geometry if row.get('sequence')==sequence and row.get('root')==0x4b7f70 and 'CALL_pc'in row];need(len(owners)==7,'Exact genuine seven tree allocation occurrences per relative-order125 case');owner_index=[0]")
 for a,b in [("'phase/0/0.bin'","f'phase/{sequence}/77.bin'"),("'phase/0/0/fs-events.bin'","f'phase/{sequence}/77/fs-events.bin'"),("'phase/0/0/api-ledger.bin'","f'phase/{sequence}/77/api-ledger.bin'"),("'phase/0/0/lockit-snapshots.bin'","f'phase/{sequence}/77/lockit-snapshots.bin'"),("f'phase/0/0/api-initial/{api_index}/bytes.bin'","f'phase/{sequence}/77/api-initial/{api_index}/bytes.bin'")]:one(a,b)
 one("result['observer_patches']=patches;result['reached_original_PCs']=machine.PCs;passed=True", "result['observer_patches']=patches;result['reached_original_PCs']=machine.PCs;result['sequence']=sequence;result['phase']=77;passed=True")
 one("main(sys.argv[1],ROOT/(sys.argv[2]if len(sys.argv)>2 else'tools/m4-tree-source/game_model.py'))", "main(sys.argv[1],ROOT/(sys.argv[2]if len(sys.argv)>2 else'tools/m4-tree-source/game_model_v4.py'),int(sys.argv[3]))")
 target=ROOT/'tools/m4-tree-source/compare_original125_prefix.py';assert not target.exists();target.write_text(s)
 out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True)
 report=dict(passed=True,scope='Unexecuted six genuine original125 tree-phase local semantic comparison adapter; persistent full-native schedule proof remains separate',files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))})
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])

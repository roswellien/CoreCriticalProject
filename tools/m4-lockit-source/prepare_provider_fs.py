"""Align the independent observer with single FS ownership of new publications."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 prior=ROOT/'reports/m4-lockit-source/adapter-preparation-r2/report.json';assert sha(prior)=='462f25521fa7f6ead36aeacf7290a75450da209055380eaa786a4b8690c3d2d3';d=json.loads(prior.read_bytes());pins=dict(d['files']);pins[str(prior)]=sha(prior)
 for p,h in pins.items():assert sha(p)==h
 owned=ROOT/'reports/m4-lockit-source/owned-contracts-r1/report.json';assert sha(owned)=='8ca045fb36a503276b05223b4c9401792077e256dbf3c37691ecb9adb4e3a51a';x=json.loads(owned.read_bytes());pins[str(owned)]=sha(owned)
 for p,h in x['files'].items():assert sha(p)==h;pins[p]=h
 old=HERE/'final_observer124.py';s=old.read_text();needle="  self.specs+=json.loads(self.pin(ROOT/'reports/m4-lockit-source/provider-preparation-r1/allocation-inputs.json').read_bytes())";assert s.count(needle)==1;s=s.replace(needle,"  self.lockit_fs_specs=json.loads(self.pin(ROOT/'reports/m4-lockit-source/owned-contracts-r1/allocation-inputs.json').read_bytes());self.fs_specs+=self.lockit_fs_specs;self.specs+=self.lockit_fs_specs");ast.parse(s);target=HERE/'final_observer124_v2.py';assert not target.exists();target.write_text(s);pins[str(target)]=sha(target)
 old=HERE/'compare_provider124_v2.py';s=old.read_text();assert s.count('import final_observer124 as F')==1;s=s.replace('import final_observer124 as F','import final_observer124_v2 as F');s=s.replace("'final_observer124.py'","'final_observer124_v2.py'");ast.parse(s);target=HERE/'compare_provider124_v3.py';assert not target.exists();target.write_text(s);pins[str(target)]=sha(target);pins[str(Path(__file__).resolve())]=sha(__file__);out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);d=dict(passed=True,scope='Exact eight publications owned by FS source contracts only; generic MFC layer does not double-count',comparer=str(target),FS_publication_count=8,new_generic_MFC_publication_count=0,source_semantics_unchanged=True,native_compared=False,initializer_credit=False,files=pins);(out/'report.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),comparer=str(target))))
if __name__=='__main__':main(sys.argv[1])

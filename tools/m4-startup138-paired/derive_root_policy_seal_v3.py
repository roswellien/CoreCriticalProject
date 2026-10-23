"""Pin the independently reviewed lock13 whole-object proof and inverses."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 parent=Path(__file__).with_name('root_seal_current_policy_v2.py');text=parent.read_text()
 old=" path=pin(R/'tools/m4-startup138-paired/preflight_comparer_v7.py')"
 new=""" read(R/'reports/m4-startup138-paired/CRT-lock13-domain-r2/report.json','6bf6c226e40dea50912fb126eaaa97715af4aadd436189114ec292f599a161eb')
 read(R/'reports/m4-startup138-paired/CRT-lock13-helper-preflight-r2/report.json','3a34fb5c22458cd670903c89f9e4cb60af25a967aa2b5869f95a8f53845d196c')
 path=pin(R/'tools/m4-startup138-paired/preflight_comparer_v7.py')"""
 assert text.count(old)==1;newtext=text.replace(old,new);assert newtext.replace(new,old)==text
 q=parent.with_name('root_seal_current_policy_v3.py');assert not q.exists();q.write_text(newtext)
 out=R/'reports/m4-startup138-paired/root-seal-derivative-r3';assert not out.exists();out.mkdir()
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,exact_inverse=True,scope='Root lock13 physical proof pinning only; seal remains uninvoked',initializer_credit=0,files={str(x.resolve()):sha(x)for x in(parent,q,Path(__file__))}),indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()

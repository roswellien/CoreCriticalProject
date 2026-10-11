"""Additive exact seventeen-pair MSVCP source API profile for125 roots."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    base=ROOT/'tools/m4-lockit-source/responses_v3.py';s=base.read_text()
    s=s.replace("CS=0x78145640","CS=0x78145640\nEXPECTED_LOCKIT_CALLS=34")
    for a,b in [('len(self.lockit_images)==8','len(self.lockit_images)==EXPECTED_LOCKIT_CALLS'),('Eight complete actual native CS40','Complete actual native CS40'),("self.lockit_image_index==8 and e['enters']==e['leaves']==4", "self.lockit_image_index==EXPECTED_LOCKIT_CALLS and e['enters']==e['leaves']==EXPECTED_LOCKIT_CALLS//2"),('All four rooted constructor/destructor API pairs','All recovered rooted constructor/destructor API pairs')]:
        assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    target=ROOT/'tools/m4-tree-source/responses125.py';assert not target.exists();target.write_text(s)
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True)
    report=dict(passed=True,scope='Unexecuted API response profile; accepted4pairs plus exact13new treepairs, every wholeCS40/guest24 source relation retained',expected_source_calls=34,expected_pairs=17,candidate_AFTER_seed=False,files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])

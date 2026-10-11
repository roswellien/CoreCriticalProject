"""Prepare the additive current131 inherited provider and dependency reviews."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    files={};changes={}
    def pin(p):
        p=Path(p).resolve();files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
    for original,target in [('review_provider130_v2.py','review_provider131.py'),('seal_source130_closure.py','seal_source131_closure.py')]:
        p=pin(R/'tools/m4-tree-review'/original);t=p.read_text();delta=[]
        def one(a,b):
            nonlocal t
            assert t.count(a)==1,(original,a,t.count(a));t=t.replace(a,b);delta.append(dict(before=a,after=b))
        one("p=R/'reports/m4-formatting-source/native130-provider-r1/report.json'", "p=Path(sys.argv[2]).resolve()")
        one("read(p,'1ac217828913db6c1efe91cb6a1b3c410b946bac883064856311e2845e7fdbfd')", 'read(p,sys.argv[3])')
        if original.startswith('review_provider'):
            start="closure=read(R/'reports/m4-tree-review/source130-closure-r1/report.json','a831d215c1465ebf6af484416e8ccba600da73515a9c7ca9507ee869a0062e4c');loaded=read(R/'reports/m4-tree-review/loaded-input130-r1/report.json','66f3b663b5c66da5d40e217fb40b2686c2b2c402dd3f2640f977db9a6d1f7ba4')"
            one(start,"closure=read(Path(sys.argv[4]).resolve(),sys.argv[5])")
            one("r['passed']and r['reader_closed']and closure['passed']and loaded['passed']and closure['source_provider_sha256']==loaded['native_source_sha256']==sha(p)", "r['passed']and r['reader_closed']and closure['passed']and closure['source_provider_sha256']==sha(p)")
            one("'57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1'", "'e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57'")
            t=t.replace("lineage['native_preparation']", "lineage['inherited_native_preparation']").replace("lineage['native_preparation_sha256']", "lineage['inherited_native_preparation_sha256']")
            one("and j['native_preparation_sha256']==lineage['inherited_native_preparation_sha256']", "and sha(Path(j['native_library']).parent/'report.json')==lineage['inherited_native_preparation_sha256']")
            one('persistent130_sequences=12,persistent_phases=1560,whole_page_BEFORE=71760,whole_page_AFTER=71760', 'persistent131_sequences=12,persistent_phases=1572,whole_page_BEFORE=72312,whole_page_AFTER=72312')
            one('reviewed_full_source_phases=1560,reviewed_whole_source_page_endpoints=143520', 'reviewed_full_source_phases=1572,reviewed_whole_source_page_endpoints=144624')
            one("'tools/m4-formatting-source/compare_provider130_v6.py'", "'tools/m4-joint-startup131/compare_provider_v5.py'")
            one("'tools/m4-formatting-source/continuity130.py'", "'tools/m4-joint-startup131/continuity131.py'")
            one("pin(R/'tools/m4-tree-review/review_provider130.py');passed=True", "pin(R/'tools/m4-tree-review/review_provider130_v2.py');passed=True")
        else:
            one("entry=R/'tools/m4-formatting-source/compare_provider130_v6.py'", "entry=R/'tools/m4-joint-startup131/compare_provider_v5.py'")
        t=t.replace('source/provider130', 'source/provider131').replace('current130_bounded_source','current131_bounded_source')
        ast.parse(t);q=R/'tools/m4-tree-review'/target;assert not q.exists();q.write_text(t);pin(q);changes[target]=delta
    pin(__file__)
    r=dict(passed=True,scope='Unexecuted exact inherited provider and observed source closure reviews for current131; loaded original/native association remains the separate current paired input gate; all physical API/private/provider predicates preserved',changes=changes,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])

"""Adapt immutable original130 literal comparers to current131 raw exports."""
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
OLD = ROOT / 'tools/m4-startup130-original'
V = '9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f'
P = '1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb'
B = 'f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d'
R = 'e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed'
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def need(value,label):
    if not value:raise ValueError(label)
def main(name):
    out=ROOT/'reports/m4-startup131-original'/name;need(not out.exists(),'Fresh additive preparation');out.mkdir(parents=True)
    pins={};hunks=[]
    def pin(path,digest=None):
        path=Path(path).resolve();need(path.suffix.lower()!='.mwb','No capture archive in preparation');actual=sha(path);need(digest is None or digest==actual,'Exact immutable source input');pins[str(path)]=actual;return path
    for path,h in [(ROOT/'reports/m4-startup131-original/validation-r2/report.json',V),(ROOT/'reports/m4-startup131-original/preparation-r4/report.json',P),(ROOT/'reports/m4-startup131-original/build-r3/build.json',B),(ROOT/'reports/m4-tree-review/original131-prelaunch-r4/report.json',R)]:
        need(json.loads(pin(path,h).read_bytes())['passed'],'Current genuine observations and actual compiled observer admission')
    common=[('m4-startup130-original','m4-startup131-original'),('91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca',V),('8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814',P),('3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103',B),('bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127',R),('original130-prelaunch-r7','original131-prelaunch-r4'),('preparation-r2','preparation-r4'),('build-r2','build-r3'),('current-original130','current-original131'),('original130','original131'),('across130 phases','across131 phases')]
    generated={}
    for filename in ['old4_source.py','format_source_v4.py','tree_source.py']:
        before=pin(OLD/filename).read_text();text=before
        for a,b in common:text=text.replace(a,b)
        # Dependency lineage remains physically pinned, rather than inventing
        # a nonexistent copied original130 preparation generator.
        text=text.replace("ROOT/'tools/m4-startup131-original/derive_old4_source.py'", "ROOT/'tools/m4-startup130-original/derive_old4_source.py'")
        text=text.replace("if path.suffix.lower()=='.mwb':need(path.is_relative_to(ROOT/'reports/m4-startup131-original/execution-r2'),'No inherited or native capture in audited original source gate')", "if path.suffix.lower()=='.mwb':need(False,'No archive may be opened by the current raw-export source gate')")
        text=text.replace("if path.suffix.lower()=='.mwb':need(path.is_relative_to(R/'reports/m4-startup131-original/execution-r2'),'Only the one current-original131 archive')", "if path.suffix.lower()=='.mwb':need(False,'No archive may be opened by the current raw-export source gate')")
        if filename=='old4_source.py':
            text=text.replace("len(p['order'])==130", "len(p['order'])==131")
            old="D=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','Lockit_original_direct');reader=D.DirectSet(v['original_capture'],pin)"
            new="E=own(ROOT/'tools/m4-startup131-original/export_reader.py','original131_raw_export');reader=E.ExportReader(sys.argv[2],sys.argv[3],'original',pin);need(Path(reader.path).resolve()==Path(v['original_capture']).resolve(),'Current genuine original transport identity')"
            need(text.count(old)==1,'One direct archive constructor');text=text.replace(old,new)
            text=text.replace("try:result,_,_=verify(reader,out)","try:result,_,_=verify(reader,out)")
            text=text.replace('recursive_workspace_source_reads_sealed=True,','recursive_workspace_source_reads_sealed=True,capture_archive_opened=False,raw_export_report_path=str(Path(sys.argv[2]).resolve()),raw_export_report_sha256=sys.argv[3],')
        elif filename=='tree_source.py':
            text=text.replace("tree_phase==78", "tree_phase==79")
        target=TOOLS/filename;need(not target.exists(),'Fresh generated source version');target.write_text(text)
        pin(target);generated[filename]=str(target.resolve());hunks.append(dict(before=str((OLD/filename).resolve()),before_sha256=sha(OLD/filename),after=str(target.resolve()),after_sha256=sha(target),changes='Current immutable observations/preparation/build/observer bindings,131 order and tree phase79; archive constructors replaced by sealed raw export only; literal model/operand/API/byteflow predicates unchanged'))
    pin(TOOLS/'export_reader.py');pin(__file__)
    path=out/'lineage.json';path.write_text(json.dumps(hunks,indent=2)+'\n');pin(path)
    report=dict(passed=True,scope='Prepared current131 inherited130 literal original source comparers. Literal bodies and all operand/byteflow/normalization predicates retained; fresh current actual process bindings and exact raw-export adapter. No original/native archive opened or semantic comparison executed.',original_validation_sha256=V,original_preparation_sha256=P,original_build_sha256=B,current_original_compiled_review_sha256=R,generated=generated,files=pins,capture_reader_opened=False,source_comparison_executed=False,initializer_credit=0)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
